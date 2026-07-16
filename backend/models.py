"""Typed API and workflow models."""

import json
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from rag.models import RetrievalEvent

from .workspace import RunWorkspace


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class RunStage(str, Enum):
    queued = "queued"
    briefing = "briefing"
    planning = "planning"
    developing = "developing"
    testing = "testing"
    repairing = "repairing"
    reporting = "reporting"
    complete = "complete"
    cancelled = "cancelled"


class AttemptStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    infrastructure = "infrastructure"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    request: str = Field(min_length=1)


class RunResponse(BaseModel):
    run_id: UUID
    status: RunStatus
    report: str
    retrieval_events: tuple[RetrievalEvent, ...] = ()


class RunEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage: RunStage
    message: str
    created_at: datetime = Field(default_factory=utc_now)


class RunAttempt(BaseModel):
    model_config = ConfigDict(frozen=True)

    sequence: int = Field(ge=1)
    candidate_attempt: int | None = Field(default=None, ge=1)
    status: AttemptStatus
    failure_kind: str | None = None
    repair_target: str | None = None
    test_results: str
    application_code: str = ""
    test_code: str = ""


class RunArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    kind: str
    content: str


class DevelopmentPlan(BaseModel):
    file_name: str = Field(pattern=r"^[a-z][a-z0-9_]*\.py$")
    test_file_name: str = Field(pattern=r"^test_[a-z][a-z0-9_]*\.py$")
    developer_task: str = Field(min_length=1)
    tester_task: str = Field(min_length=1)

    @field_validator("developer_task", "tester_task", mode="before")
    @classmethod
    def normalize_structured_instructions(cls, value: object) -> object:
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return value

    @model_validator(mode="after")
    def validate_matching_file_names(self) -> "DevelopmentPlan":
        if self.test_file_name != f"test_{self.file_name}":
            raise ValueError(
                "Test file name must be derived from the application file."
            )
        return self


class RunState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    run_id: UUID = Field(default_factory=uuid4)
    request: str
    workspace: RunWorkspace = Field(default_factory=RunWorkspace)
    status: RunStatus = RunStatus.pending
    stage: RunStage = RunStage.queued
    attempts: int = 0
    attempt_history: list[RunAttempt] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)
    technical_brief: str | None = None
    plan: DevelopmentPlan | None = None
    test_results: str | None = None
    retrieval_events: list[RetrievalEvent] = Field(default_factory=list)
    report: str | None = None


class RunSnapshot(BaseModel):
    run_id: UUID
    request: str
    status: RunStatus
    stage: RunStage
    attempts_used: int = Field(ge=0)
    max_attempts: int = Field(ge=1)
    cancel_requested: bool = False
    created_at: datetime
    updated_at: datetime
    technical_brief: str | None = None
    plan: DevelopmentPlan | None = None
    test_results: str | None = None
    report: str | None = None
    attempts: tuple[RunAttempt, ...] = ()
    events: tuple[RunEvent, ...] = ()
    artifacts: tuple[RunArtifact, ...] = ()
    retrieval_events: tuple[RetrievalEvent, ...] = ()
    error: str | None = None
