import asyncio
import logging
from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from app.core.config import Settings
from app.providers.embeddings import create_embeddings
from app.providers.llm import create_llm
from app.providers.vector_store import VectorStore, create_vector_store
from app.rag.graph import build_qa_graph
from app.services.errors import IndexUnavailableError, ModelCallError, ModelTimeoutError

logger = logging.getLogger(__name__)
_MAX_MODEL_ATTEMPTS = 3
_RETRY_BASE_SECONDS = 0.25


class SourceResult(TypedDict):
    document: str
    chunk_id: str
    score: float
    snippet: str


class QAResult(TypedDict):
    answer: str
    answered: bool
    sources: list[SourceResult]


def _is_transient(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 429 or (isinstance(status_code, int) and status_code >= 500):
        return True
    if isinstance(exc, (ConnectionError, OSError)):
        return True
    name = type(exc).__name__.lower()
    return "connection" in name or "connecterror" in name


class QAService:
    def __init__(
        self,
        settings: Settings,
        llm: BaseChatModel,
        vector_store: VectorStore,
    ) -> None:
        self.settings = settings
        self._llm = llm
        self._vector_store = vector_store
        self._llm_semaphore = asyncio.Semaphore(settings.max_concurrent_llm_calls)
        self._graph = build_qa_graph(
            llm,
            vector_store,
            settings.retrieval_score_threshold,
            invoke_llm=self._invoke_llm,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "QAService":
        return cls(
            settings,
            create_llm(settings),
            create_vector_store(settings, create_embeddings(settings)),
        )

    async def health(self) -> dict[str, str | bool | int]:
        chunks = await asyncio.to_thread(self._vector_store.count)
        return {
            "status": "ok",
            "llm_provider": self.settings.llm_provider,
            "embedding_provider": self.settings.embedding_provider,
            "index_loaded": chunks > 0,
            "index_chunks": chunks,
        }

    async def ask(self, question: str, top_k: int | None = None) -> QAResult:
        if await asyncio.to_thread(self._vector_store.count) == 0:
            raise IndexUnavailableError

        result = await self._graph.ainvoke(
            {"question": question, "top_k": top_k or self.settings.retrieval_top_k}
        )
        sources: list[SourceResult] = [
            {
                "document": item["document"].metadata["document"],
                "chunk_id": item["document"].metadata["chunk_id"],
                "score": item["score"],
                "snippet": _snippet(item["document"]),
            }
            for item in result["documents"]
        ]
        return {"answer": result["answer"], "answered": result["answered"], "sources": sources}

    async def _invoke_llm(self, prompt: object) -> BaseMessage:
        for attempt in range(_MAX_MODEL_ATTEMPTS):
            try:
                async with self._llm_semaphore:
                    return await asyncio.wait_for(
                        self._llm.ainvoke(prompt), timeout=self.settings.llm_timeout_seconds
                    )
            except TimeoutError as exc:
                logger.warning("LLM request timed out")
                raise ModelTimeoutError from exc
            except Exception as exc:
                if attempt < _MAX_MODEL_ATTEMPTS - 1 and _is_transient(exc):
                    delay = _RETRY_BASE_SECONDS * (2**attempt)
                    logger.warning(
                        "Transient LLM error; retrying attempt %d/%d in %.2fs",
                        attempt + 1,
                        _MAX_MODEL_ATTEMPTS,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.exception("LLM request failed")
                raise ModelCallError from exc
        raise ModelCallError


def _snippet(document: Document, limit: int = 240) -> str:
    text = " ".join(document.page_content.split())
    return text if len(text) <= limit else f"{text[:limit].rstrip()}..."
