import hashlib
import math
import re

from langchain_core.embeddings import Embeddings

from app.core.config import Settings

FAKE_EMBEDDING_SIZE = 64


class FakeEmbeddings(Embeddings):
    """Deterministic hashed bag-of-words embeddings; texts sharing words get similar vectors."""

    def __init__(self, size: int = FAKE_EMBEDDING_SIZE) -> None:
        self._size = size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * self._size
        for token in re.findall(r"\w+", text.lower()):
            bucket = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big")
            vector[bucket % self._size] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def embedding_model_name(settings: Settings) -> str:
    match settings.embedding_provider:
        case "openai":
            return settings.openai_embedding_model
        case "ollama":
            return settings.ollama_embedding_model
        case "fake":
            return f"fake-{FAKE_EMBEDDING_SIZE}"
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def create_embeddings(settings: Settings) -> Embeddings:
    match settings.embedding_provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(
                model=settings.openai_embedding_model,
                api_key=settings.openai_api_key,
                timeout=settings.llm_timeout_seconds,
                max_retries=0,
            )
        case "ollama":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(
                model=settings.ollama_embedding_model,
                base_url=settings.ollama_base_url,
                client_kwargs={"timeout": settings.llm_timeout_seconds},
            )
        case "fake":
            return FakeEmbeddings()
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
