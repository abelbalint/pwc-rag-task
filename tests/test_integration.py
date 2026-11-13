import asyncio
import json
import urllib.error
import urllib.request

import pytest
from langchain_core.documents import Document
from pydantic import ValidationError

from app.core.config import Settings
from app.providers.embeddings import create_embeddings
from app.providers.llm import create_llm
from app.providers.vector_store import create_vector_store
from app.services.qa import QAService

pytestmark = pytest.mark.integration


def _configured_settings() -> Settings:
    try:
        settings = Settings()
    except ValidationError as exc:
        pytest.skip(f"Integration provider configuration is incomplete: {exc.errors()[0]['msg']}")

    if "fake" in (settings.llm_provider, settings.embedding_provider):
        pytest.skip("Integration tests require a real LLM and embedding provider")

    if "ollama" in (settings.llm_provider, settings.embedding_provider):
        try:
            with urllib.request.urlopen(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=2
            ) as response:
                available = {
                    item["name"].removesuffix(":latest")
                    for item in json.load(response).get("models", [])
                }
        except (OSError, urllib.error.URLError) as exc:
            pytest.skip(f"Ollama is unavailable at {settings.ollama_base_url}: {exc}")

        required = set()
        if settings.llm_provider == "ollama":
            required.add(settings.ollama_llm_model)
        if settings.embedding_provider == "ollama":
            required.add(settings.ollama_embedding_model)
        missing = required - available
        if missing:
            pytest.skip(f"Ollama models are not downloaded: {', '.join(sorted(missing))}")

    return settings


def test_real_providers_answer_from_indexed_context(tmp_path) -> None:
    configured = _configured_settings()
    settings = configured.model_copy(
        update={
            "storage_dir": str(tmp_path),
            "retrieval_score_threshold": 0.0,
            "llm_timeout_seconds": max(configured.llm_timeout_seconds, 120),
        }
    )
    embeddings = create_embeddings(settings)
    store = create_vector_store(settings, embeddings)
    store.replace_documents(
        [
            Document(
                page_content=(
                    "The Acme archive VPN support phone number is +1 555 010 0777. "
                    "This number is reserved for the integration test."
                ),
                metadata={
                    "document": "integration-vpn.md",
                    "section": "Support contact",
                    "chunk_id": "integration-vpn:0:0",
                },
            )
        ]
    )
    service = QAService(settings, create_llm(settings), store)

    result = asyncio.run(service.ask("What is the archive VPN support phone number?", top_k=1))

    assert result["answered"] is True
    assert result["answer"].strip()
    assert len(result["sources"]) == 1
    assert result["sources"][0]["document"] == "integration-vpn.md"
