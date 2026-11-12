import asyncio
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from app.core.config import Settings
from app.main import create_app
from app.services.qa import QAService


class FakeVectorStore:
    def __init__(self, *, has_index: bool = True, results: list | None = None) -> None:
        self.has_index = has_index
        self.results = results or []

    def count(self) -> int:
        return int(self.has_index)

    def search(self, query: str, top_k: int) -> list:
        return self.results[:top_k]

    def replace_documents(self, documents: list[Document]) -> None:
        self.results = [(document, 0.9) for document in documents]
        self.has_index = bool(documents)


class FakeLLM:
    def __init__(self, action: Callable | Exception | None = None) -> None:
        self.action = action
        self.calls = 0

    async def ainvoke(self, prompt, **kwargs) -> AIMessage:
        self.calls += 1
        if isinstance(self.action, Exception):
            raise self.action
        if self.action is not None:
            return await self.action(prompt)
        return AIMessage(content="Reset your password at the self-service portal.")


def make_service(
    *,
    llm: FakeLLM | None = None,
    has_index: bool = True,
    results: list | None = None,
    timeout: float = 0.1,
) -> tuple[QAService, FakeLLM]:
    document = Document(
        page_content="Reset a forgotten password at https://password.acme.example.",
        metadata={
            "document": "password-reset-and-mfa.md",
            "section": "Resetting",
            "chunk_id": "pwd:0:0",
        },
    )
    model = llm or FakeLLM()
    settings = Settings(
        _env_file=None,
        llm_provider="fake",
        embedding_provider="fake",
        llm_timeout_seconds=timeout,
    )
    service = QAService(
        settings,
        model,
        FakeVectorStore(
            has_index=has_index,
            results=results if results is not None else [(document, 0.9)],
        ),
    )
    return service, model


def post_ask(service: QAService, payload: object, *, headers: dict | None = None):
    app = create_app(qa_service_override=service)
    with TestClient(app, raise_server_exceptions=False) as client:
        return client.post("/ask", json=payload, headers=headers or {})


def test_ask_returns_answer_sources_and_request_id() -> None:
    service, _ = make_service()

    response = post_ask(
        service,
        {"question": "How do I reset my password?", "top_k": 2},
        headers={"X-Request-ID": "interview-test-123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answered"] is True
    assert body["sources"][0]["document"] == "password-reset-and-mfa.md"
    assert body["sources"][0]["chunk_id"] == "pwd:0:0"
    assert body["sources"][0]["score"] == 0.9
    assert body["request_id"] == "interview-test-123"
    assert response.headers["X-Request-ID"] == "interview-test-123"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": ""},
        {"question": "  \t\n"},
        {"question": "x" * 1001},
        {"question": "valid", "top_k": 0},
        {"question": "valid", "top_k": 11},
    ],
)
def test_invalid_ask_payload_has_unified_error(payload: object) -> None:
    service, _ = make_service()

    response = post_ask(service, payload, headers={"X-Request-ID": "invalid-request"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["request_id"] == "invalid-request"
    assert response.headers["X-Request-ID"] == "invalid-request"


def test_no_relevant_results_skip_model() -> None:
    service, llm = make_service(results=[])

    response = post_ask(service, {"question": "Where is the office?"})

    assert response.status_code == 200
    assert response.json()["answered"] is False
    assert response.json()["sources"] == []
    assert llm.calls == 0


def test_empty_index_returns_503() -> None:
    service, _ = make_service(has_index=False, results=[])

    response = post_ask(service, {"question": "Where is the office?"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "index_unavailable"


def test_model_error_returns_502() -> None:
    service, _ = make_service(llm=FakeLLM(action=ValueError("provider details")))

    response = post_ask(service, {"question": "How do I reset my password?"})

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "model_error"
    assert "provider details" not in response.text


def test_model_timeout_returns_504() -> None:
    async def slow_model(prompt) -> AIMessage:
        await asyncio.sleep(0.1)
        return AIMessage(content="late answer")

    service, _ = make_service(llm=FakeLLM(action=slow_model), timeout=0.01)

    response = post_ask(service, {"question": "How do I reset my password?"})

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "model_timeout"


def test_unexpected_error_is_generic_and_gets_request_id(monkeypatch) -> None:
    service, _ = make_service()

    def broken_count() -> int:
        raise RuntimeError("private storage details")

    monkeypatch.setattr(service._vector_store, "count", broken_count)
    response = post_ask(service, {"question": "Where is the office?"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private storage details" not in response.text
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_openapi_contains_ask_example() -> None:
    service, _ = make_service()
    app = create_app(qa_service_override=service)

    with TestClient(app) as client:
        specification = client.get("/openapi.json").json()
        schemas = specification["components"]["schemas"]

    assert schemas["AskRequest"]["examples"] == [
        {"question": "How do I connect to the company VPN?", "top_k": 4}
    ]
    assert schemas["ErrorResponse"]["examples"][0]["error"]["code"] == "validation_error"
    responses = specification["paths"]["/ask"]["post"]["responses"]
    assert (
        "#/components/schemas/ErrorResponse"
        in responses["422"]["content"]["application/json"]["schema"]["$ref"]
    )


def test_transient_model_failure_is_retried() -> None:
    class RetryOnce:
        calls = 0

        async def __call__(self, prompt) -> AIMessage:
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("temporary network issue")
            return AIMessage(content="Recovered answer.")

    retry_once = RetryOnce()
    service, llm = make_service(llm=FakeLLM(action=retry_once))

    response = post_ask(service, {"question": "How do I reset my password?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Recovered answer."
    assert retry_once.calls == 2
    assert llm.calls == 2
