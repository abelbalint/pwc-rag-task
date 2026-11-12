from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.services.qa import QAService


def test_health_reports_providers_and_empty_index() -> None:
    service = Mock(spec=QAService)
    service.health = AsyncMock(
        return_value={
            "status": "ok",
            "llm_provider": "ollama",
            "embedding_provider": "ollama",
            "index_loaded": False,
            "index_chunks": 0,
        }
    )
    app = create_app(qa_service_override=service)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["index_loaded"] is False
    assert body["index_chunks"] == 0


def test_openai_requires_api_key() -> None:
    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        Settings(_env_file=None, llm_provider="openai", openai_api_key=None)


def test_ollama_needs_no_api_key() -> None:
    settings = Settings(_env_file=None, llm_provider="ollama", embedding_provider="ollama")

    assert settings.openai_api_key is None
