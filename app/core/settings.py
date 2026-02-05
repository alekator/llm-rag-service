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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    if not s.database_url:
        raise RuntimeError("APP_DATABASE_URL is not set (check .env or environment).")
    return s


openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
openai_embeddings_model: str = Field(
    default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDINGS_MODEL"
)
