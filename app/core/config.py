from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Provider = Literal["openai", "ollama", "fake"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: Provider = "ollama"
    embedding_provider: Provider = "ollama"

    openai_api_key: SecretStr | None = None
    openai_llm_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    llm_timeout_seconds: float = Field(default=60.0, gt=0)
    max_concurrent_llm_calls: int = Field(default=4, ge=1)
    retrieval_top_k: int = Field(default=4, ge=1, le=10)
    retrieval_score_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    docs_dir: str = "data/docs"
    storage_dir: str = "storage"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _require_openai_key(self) -> Self:
        uses_openai = "openai" in (self.llm_provider, self.embedding_provider)
        if uses_openai and not (self.openai_api_key and self.openai_api_key.get_secret_value()):
            raise ValueError("OPENAI_API_KEY must be set when the OpenAI provider is selected")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
