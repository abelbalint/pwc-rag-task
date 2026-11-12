from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.core.config import Settings

FAKE_LLM_RESPONSE = "This is a fake answer."


def create_llm(settings: Settings) -> BaseChatModel:
    match settings.llm_provider:
        case "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=settings.openai_llm_model,
                api_key=settings.openai_api_key,
                timeout=settings.llm_timeout_seconds,
                temperature=0,
                max_retries=0,  # retries are handled by the QA service
            )
        case "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=settings.ollama_llm_model,
                base_url=settings.ollama_base_url,
                temperature=0,
                client_kwargs={"timeout": settings.llm_timeout_seconds},
            )
        case "fake":
            return FakeListChatModel(responses=[FAKE_LLM_RESPONSE])
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
