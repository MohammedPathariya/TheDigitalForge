"""Typed API and workflow models."""

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rag.models import RetrievalEvent

from .workspace import RunWorkspace


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class RunRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    request: str = Field(min_length=1)


class RunResponse(BaseModel):
    run_id: UUID
    status: RunStatus
    report: str
    retrieval_events: tuple[RetrievalEvent, ...] = ()


class DevelopmentPlan(BaseModel):
    file_name: str = Field(pattern=r"^[a-z][a-z0-9_]*\.py$")
    test_file_name: str = Field(pattern=r"^test_[a-z][a-z0-9_]*\.py$")
    developer_task: str = Field(min_length=1)
    tester_task: str = Field(min_length=1)

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
    attempts: int = 0
    technical_brief: str | None = None
    plan: DevelopmentPlan | None = None
    test_results: str | None = None
    retrieval_events: list[RetrievalEvent] = Field(default_factory=list)
    report: str | None = None
