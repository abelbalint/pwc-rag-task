import hashlib
import re
from typing import Protocol

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.providers.embeddings import embedding_model_name


class VectorStore(Protocol):
    def replace_documents(self, documents: list[Document]) -> None: ...

    def search(self, query: str, top_k: int) -> list[tuple[Document, float]]: ...

    def count(self) -> int: ...


def collection_name_for(settings: Settings) -> str:
    model_name = embedding_model_name(settings)
    slug = re.sub(r"[^a-z0-9]+", "_", model_name.lower()).strip("_")[:40] or "model"
    suffix = hashlib.sha256(model_name.encode()).hexdigest()[:8]
    return f"acme_helpdesk_{slug}_{suffix}"


class ChromaVectorStore:
    def __init__(self, store: Chroma) -> None:
        self._store = store

    def replace_documents(self, documents: list[Document]) -> None:
        existing_ids = self._store.get(include=[])["ids"]
        if existing_ids:
            self._store.delete(ids=existing_ids)
        if documents:
            self._store.add_documents(
                documents,
                ids=[document.metadata["chunk_id"] for document in documents],
            )

    def search(self, query: str, top_k: int) -> list[tuple[Document, float]]:
        return self._store.similarity_search_with_relevance_scores(query, k=top_k)

    def count(self) -> int:
        return len(self._store.get(include=[])["ids"])


def create_vector_store(settings: Settings, embeddings: Embeddings) -> ChromaVectorStore:
    store = Chroma(
        collection_name=collection_name_for(settings),
        embedding_function=embeddings,
        persist_directory=settings.storage_dir,
        collection_metadata={
            "embedding_model": embedding_model_name(settings),
            "hnsw:space": "cosine",
        },
        collection_configuration={"hnsw": {"space": "cosine"}},
    )
    return ChromaVectorStore(store)
