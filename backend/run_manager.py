"""Thread-safe in-memory run coordination for the polling API."""

from collections.abc import Callable
from threading import Event, RLock, Thread
from typing import Protocol
from uuid import UUID, uuid4

from .config import Settings
from .models import (
    RunArtifact,
    RunEvent,
    RunResponse,
    RunSnapshot,
    RunStage,
    RunState,
    RunStatus,
    utc_now,
)
from .self_healing import sanitize_output


class Runner(Protocol):
    def run(self) -> RunResponse: ...


UpdateCallback = Callable[[RunState], None]
CancellationCheck = Callable[[], bool]
RunnerFactory = Callable[
    [str, Settings, UUID, UpdateCallback, CancellationCheck], Runner
]


class RunManager:
    """Own process-local run snapshots and execute pipelines in worker threads."""

    def __init__(self, settings: Settings, runner_factory: RunnerFactory):
        self.settings = settings
        self.runner_factory = runner_factory
        self._runs: dict[UUID, RunSnapshot] = {}
        self._cancellations: dict[UUID, Event] = {}
        self._lock = RLock()

    def start(self, request: str) -> RunSnapshot:
        run_id = uuid4()
        created_at = utc_now()
        snapshot = RunSnapshot(
            run_id=run_id,
            request=request,
            status=RunStatus.pending,
            stage=RunStage.queued,
            attempts_used=0,
            max_attempts=self.settings.max_attempts,
            created_at=created_at,
            updated_at=created_at,
            events=(RunEvent(stage=RunStage.queued, message="The run is queued."),),
        )
        cancellation = Event()
        with self._lock:
            self._runs[run_id] = snapshot
            self._cancellations[run_id] = cancellation
        Thread(
            target=self._execute,
            args=(run_id, request, cancellation),
            name=f"digital-forge-{run_id.hex[:8]}",
            daemon=True,
        ).start()
        return snapshot.model_copy(deep=True)

    def get(self, run_id: UUID) -> RunSnapshot | None:
        with self._lock:
            snapshot = self._runs.get(run_id)
            return snapshot.model_copy(deep=True) if snapshot is not None else None

    def cancel(self, run_id: UUID) -> RunSnapshot | None:
        with self._lock:
            snapshot = self._runs.get(run_id)
            cancellation = self._cancellations.get(run_id)
            if snapshot is None or cancellation is None:
                return None
            if snapshot.status not in {
                RunStatus.completed,
                RunStatus.failed,
                RunStatus.cancelled,
            }:
                cancellation.set()
                snapshot = snapshot.model_copy(
                    update={"cancel_requested": True, "updated_at": utc_now()}
                )
                self._runs[run_id] = snapshot
            return snapshot.model_copy(deep=True)

    def _execute(self, run_id: UUID, request: str, cancellation: Event) -> None:
        try:
            runner = self.runner_factory(
                request,
                self.settings,
                run_id,
                lambda state: self._update(run_id, state),
                cancellation.is_set,
            )
            result = runner.run()
            with self._lock:
                current = self._runs[run_id]
                self._runs[run_id] = current.model_copy(
                    update={
                        "status": result.status,
                        "stage": (
                            RunStage.cancelled
                            if result.status is RunStatus.cancelled
                            else RunStage.complete
                        ),
                        "report": result.report,
                        "retrieval_events": result.retrieval_events,
                        "updated_at": utc_now(),
                    }
                )
        except Exception as exc:
            error = sanitize_output(f"{type(exc).__name__}: {exc}")
            with self._lock:
                current = self._runs[run_id]
                self._runs[run_id] = current.model_copy(
                    update={
                        "status": RunStatus.failed,
                        "stage": RunStage.complete,
                        "error": error,
                        "updated_at": utc_now(),
                        "events": (
                            *current.events,
                            RunEvent(
                                stage=RunStage.complete,
                                message="The pipeline stopped because an error occurred.",
                            ),
                        ),
                    }
                )

    def _update(self, run_id: UUID, state: RunState) -> None:
        artifacts: list[RunArtifact] = []
        if state.plan is not None:
            application_code = state.workspace.read(state.plan.file_name)
            test_code = state.workspace.read(state.plan.test_file_name)
            if application_code is not None:
                artifacts.append(
                    RunArtifact(
                        path=state.plan.file_name,
                        kind="application",
                        content=application_code,
                    )
                )
            if test_code is not None:
                artifacts.append(
                    RunArtifact(
                        path=state.plan.test_file_name,
                        kind="tests",
                        content=test_code,
                    )
                )
        with self._lock:
            current = self._runs[run_id]
            self._runs[run_id] = current.model_copy(
                update={
                    "status": state.status,
                    "stage": state.stage,
                    "attempts_used": state.attempts,
                    "technical_brief": state.technical_brief,
                    "plan": state.plan,
                    "test_results": state.test_results,
                    "report": state.report,
                    "attempts": tuple(state.attempt_history),
                    "events": tuple(state.events),
                    "artifacts": tuple(artifacts),
                    "retrieval_events": tuple(state.retrieval_events),
                    "updated_at": utc_now(),
                }
            )
