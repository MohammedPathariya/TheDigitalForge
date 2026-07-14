"""Typed API and workflow models."""

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

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


class DevelopmentPlan(BaseModel):
    file_name: str
    test_file_name: str
    developer_task: str
    tester_task: str


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
    report: str | None = None
