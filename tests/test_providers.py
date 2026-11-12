from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import Settings
from app.providers.embeddings import (
    FAKE_EMBEDDING_SIZE,
    FakeEmbeddings,
    create_embeddings,
    embedding_model_name,
)
from app.providers.llm import FAKE_LLM_RESPONSE, create_llm


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_fake_llm_returns_fixed_answer() -> None:
    llm = create_llm(make_settings(llm_provider="fake"))

    assert isinstance(llm, FakeListChatModel)
    assert llm.invoke("anything").content == FAKE_LLM_RESPONSE


def test_fake_embeddings_are_deterministic() -> None:
    embeddings = create_embeddings(make_settings(embedding_provider="fake"))

    assert isinstance(embeddings, FakeEmbeddings)
    first = embeddings.embed_query("vpn")
    assert first == embeddings.embed_query("vpn")
    assert len(first) == FAKE_EMBEDDING_SIZE


def test_fake_embeddings_rank_shared_words_higher() -> None:
    embeddings = FakeEmbeddings()
    query = embeddings.embed_query("how to connect vpn")
    related = embeddings.embed_query("connect to the vpn gateway")
    unrelated = embeddings.embed_query("printer toner replacement")

    def dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=True))

    assert dot(query, related) > dot(query, unrelated)


def test_ollama_providers_use_configured_models() -> None:
    settings = make_settings(
        llm_provider="ollama",
        embedding_provider="ollama",
        ollama_base_url="http://ollama:11434",
    )

    llm = create_llm(settings)
    embeddings = create_embeddings(settings)

    assert isinstance(llm, ChatOllama)
    assert llm.model == "llama3.2:3b"
    assert llm.base_url == "http://ollama:11434"
    assert isinstance(embeddings, OllamaEmbeddings)
    assert embeddings.model == "nomic-embed-text"


def test_openai_providers_use_configured_models() -> None:
    settings = make_settings(
        llm_provider="openai",
        embedding_provider="openai",
        openai_api_key="test-key",
    )

    llm = create_llm(settings)
    embeddings = create_embeddings(settings)

    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"
    assert llm.max_retries == 0
    assert isinstance(embeddings, OpenAIEmbeddings)
    assert embeddings.model == "text-embedding-3-small"


def test_embedding_model_name_depends_on_provider() -> None:
    assert embedding_model_name(make_settings(embedding_provider="ollama")) == "nomic-embed-text"
    assert embedding_model_name(make_settings(embedding_provider="fake")) == "fake-64"
    assert (
        embedding_model_name(make_settings(embedding_provider="openai", openai_api_key="k"))
        == "text-embedding-3-small"
    )
