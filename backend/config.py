"""Typed application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: str | None = Field(default=None, repr=False)
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]
    max_request_characters: int = Field(default=20_000, ge=1)
    max_attempts: int = Field(default=3, ge=1, le=3)

    def require_openai_api_key(self) -> str:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to run the pipeline.")
        return self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
