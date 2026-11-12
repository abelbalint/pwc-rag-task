from langchain_core.documents import Document

from app.core.config import Settings
from app.providers.embeddings import FakeEmbeddings
from app.providers.vector_store import collection_name_for, create_vector_store


def test_collection_name_is_distinct_by_embedding_model() -> None:
    ollama = Settings(_env_file=None, embedding_provider="ollama")
    fake = Settings(_env_file=None, embedding_provider="fake")

    assert collection_name_for(ollama) != collection_name_for(fake)


def test_chroma_store_replaces_and_retrieves_documents(tmp_path) -> None:
    settings = Settings(_env_file=None, embedding_provider="fake", storage_dir=str(tmp_path))
    store = create_vector_store(settings, FakeEmbeddings())
    vpn = Document(
        page_content="Connect to the VPN with your Acme account.",
        metadata={"document": "vpn.md", "section": "Connecting", "chunk_id": "vpn:0:0"},
    )
    printer = Document(
        page_content="Replace the printer toner cartridge.",
        metadata={"document": "printing.md", "section": "Toner", "chunk_id": "printing:0:0"},
    )

    store.replace_documents([vpn, printer])
    results = store.search("How do I connect to the VPN?", top_k=2)

    assert store.count() == 2
    assert results[0][0].metadata["document"] == "vpn.md"
    assert 0.0 <= results[0][1] <= 1.0

    store.replace_documents([vpn])

    assert store.count() == 1
    assert store.search("VPN connection", top_k=2)[0][0].metadata["chunk_id"] == "vpn:0:0"
