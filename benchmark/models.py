"""Typed benchmark tasks, executions, and result artifacts."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"


class BenchmarkTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^forge_(easy|medium)_\d{2}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    title: str
    difficulty: Difficulty
    function_name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    prompt: str
    tags: tuple[str, ...]
    time_limit_seconds: float = Field(gt=0, le=10)


class GeneratedSolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class EvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    passed: bool
    tests_passed: int = Field(ge=0)
    tests_total: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    error: str | None = None


class TaskResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    task_id: str
    task_version: str
    difficulty: Difficulty
    passed: bool
    tests_passed: int = Field(ge=0)
    tests_total: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    candidate_path: str
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


class BenchmarkReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    benchmark_version: str
    evaluator_sha256: str
    run_id: str
    model: str
    started_at: datetime
    completed_at: datetime
    tasks_passed: int = Field(ge=0)
    tasks_total: int = Field(ge=0)
    results: tuple[TaskResult, ...]

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
