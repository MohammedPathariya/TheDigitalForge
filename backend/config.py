"""Typed application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    sandbox_backend: Literal["docker", "modal"] = "docker"
    docker_sandbox_image: str = "digital-forge-sandbox:py311"
    modal_sandbox_app: str = "digital-forge-sandbox"
    sandbox_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    sandbox_memory_mib: int = Field(default=256, ge=32, le=1024)
    sandbox_cpu_cores: float = Field(default=1.0, ge=0.1, le=2.0)
    sandbox_process_limit: int = Field(default=64, ge=4, le=128)
    rag_index_path: Path = PROJECT_ROOT / "rag" / "index" / "v1"
    rag_result_limit: int = Field(default=3, ge=1, le=5)
    benchmark_results_path: Path = PROJECT_ROOT / "benchmark-results"

    def require_openai_api_key(self) -> str:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to run the pipeline.")
        return self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
