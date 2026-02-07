from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "llm-rag-service"
    env: str = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str | None = Field(default=None, validation_alias="APP_DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="APP_REDIS_URL")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
    openai_embeddings_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDINGS_MODEL"
    )

    embeddings_backend: str = Field(
        default="auto",
        validation_alias="APP_EMBEDDINGS_BACKEND",
        description="auto|openai|mock",
    )
    embeddings_dim: int = Field(
        default=1536,
        validation_alias="APP_EMBEDDINGS_DIM",
        description="Vector size for mock embeddings and DB column dimension if used",
    )

    llm_backend: str = Field(
        default="disabled",
        validation_alias="APP_LLM_BACKEND",
        description="disabled|openai",
    )
    openai_chat_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_CHAT_MODEL",
    )

    @property
    def database_url_required(self) -> str:
        if not self.database_url:
            raise RuntimeError("APP_DATABASE_URL is not set (check .env or environment).")
        return self.database_url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    rerank_backend: str = Field(
        default="disabled",
        validation_alias="APP_RERANK_BACKEND",
        description="disabled|overlap",
    )
    rerank_weight: float = Field(
        default=0.35,
        validation_alias="APP_RERANK_WEIGHT",
        description="0..1, how much overlap affects final score",
    )
    rerank_candidates_multiplier: int = Field(
        default=3,
        validation_alias="APP_RERANK_CANDIDATES_MULTIPLIER",
        description="fetch top_k * multiplier from vector search, then rerank down to top_k",
    )

    rerank_alpha: float = Field(
        default=0.7,
        validation_alias="APP_RERANK_ALPHA",
        description="weight for vector score in combined rerank",
    )
    reranker: str = Field(
        default="none",
        validation_alias="APP_RERANKER",
        description="none|overlap (rerank retrieved chunks by token overlap)",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    if not s.database_url:
        raise RuntimeError("APP_DATABASE_URL is not set (check .env or environment).")
    return s
