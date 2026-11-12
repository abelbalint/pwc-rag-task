import logging
from pathlib import Path

from app.core.config import get_settings
from app.providers.embeddings import create_embeddings
from app.providers.vector_store import create_vector_store
from app.rag.chunking import load_markdown_documents, split_documents

logger = logging.getLogger(__name__)


def ingest() -> int:
    settings = get_settings()
    source_documents = load_markdown_documents(Path(settings.docs_dir))
    if not source_documents:
        raise SystemExit(f"No Markdown documents found in {settings.docs_dir}")

    chunks = split_documents(source_documents)
    embeddings = create_embeddings(settings)
    store = create_vector_store(settings, embeddings)
    store.replace_documents(chunks)
    logger.info("Indexed %d chunks from %d documents", len(chunks), len(source_documents))
    print(f"Indexed {len(chunks)} chunks from {len(source_documents)} documents.")
    return len(chunks)


def main() -> None:
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ingest()


if __name__ == "__main__":
    main()
