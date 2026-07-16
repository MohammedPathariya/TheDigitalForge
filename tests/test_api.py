import time
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app
from backend.models import RunResponse, RunState, RunStatus
from rag.models import RetrievalEvent, RetrievedSource


class FakeRunner:
    def __init__(
        self,
        request: str,
        settings: Settings,
        run_id: UUID,
        on_update: Callable[[RunState], None],
        is_cancel_requested: Callable[[], bool],
    ):
        self.request = request
        self.settings = settings
        self.run_id = run_id
        self.on_update = on_update
        self.is_cancel_requested = is_cancel_requested

    def run(self) -> RunResponse:
        return RunResponse(
            run_id=self.run_id,
            status=RunStatus.completed,
            report=f"Completed: {self.request}",
        )


class RetrievalRunner(FakeRunner):
    def run(self) -> RunResponse:
        source = RetrievedSource(
            chunk_id="source:00",
            source_id="source",
            library="library",
            library_version="1.0.0",
            document_version="1.0.0",
            title="Reference",
            heading="Usage",
            source_url="https://example.com/reference",
            content="full retrieved chunk",
            distance=0.1,
        )
        return RunResponse(
            run_id=self.run_id,
            status=RunStatus.completed,
            report="Completed",
            retrieval_events=(RetrievalEvent(query="API usage", results=(source,)),),
        )


class CancellableRunner(FakeRunner):
    def run(self) -> RunResponse:
        for _ in range(1000):
            if self.is_cancel_requested():
                return RunResponse(
                    run_id=self.run_id,
                    status=RunStatus.cancelled,
                    report="Run cancelled.",
                )
            time.sleep(0.001)
        raise TimeoutError("Cancellation was not requested.")


def test_health() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_uses_typed_response() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.post("/run", json={"request": "  build a parser  "})

    assert response.status_code == 200
    payload = response.json()
    UUID(payload["run_id"])
    assert payload["status"] == "completed"
    assert payload["report"] == "Completed: build a parser"
    assert payload["retrieval_events"] == []


def test_run_rejects_blank_request() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.post("/run", json={"request": "   "})

    assert response.status_code == 422


def test_run_logs_retrieval_metadata_without_chunk_content() -> None:
    client = TestClient(create_app(Settings(), runner_factory=RetrievalRunner))

    response = client.post("/run", json={"request": "build an API client"})

    result = response.json()["retrieval_events"][0]["results"][0]
    assert result["source_id"] == "source"
    assert "content" not in result


def test_run_rejects_oversized_request() -> None:
    settings = Settings(max_request_characters=3)
    client = TestClient(create_app(settings, runner_factory=FakeRunner))

    response = client.post("/run", json={"request": "four"})

    assert response.status_code == 413


def test_polling_run_api_starts_and_reaches_a_terminal_state() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.post("/runs", json={"request": "build a parser"})

    assert response.status_code == 202
    run_id = response.json()["run_id"]
    assert response.json()["status"] == "pending"

    for _ in range(100):
        snapshot = client.get(f"/runs/{run_id}")
        if snapshot.json()["status"] == "completed":
            break
        time.sleep(0.01)

    assert snapshot.status_code == 200
    assert snapshot.json()["report"] == "Completed: build a parser"


def test_polling_run_api_returns_not_found() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.get("/runs/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404


def test_polling_run_api_requests_cooperative_cancellation() -> None:
    client = TestClient(create_app(Settings(), runner_factory=CancellableRunner))
    run_id = client.post("/runs", json={"request": "build a parser"}).json()["run_id"]

    cancellation = client.post(f"/runs/{run_id}/cancel")

    assert cancellation.status_code == 200
    assert cancellation.json()["cancel_requested"] is True
    for _ in range(100):
        snapshot = client.get(f"/runs/{run_id}")
        if snapshot.json()["status"] == "cancelled":
            break
        time.sleep(0.01)
    assert snapshot.json()["status"] == "cancelled"


def test_benchmark_endpoint_returns_empty_list_without_artifacts(
    tmp_path: Path,
) -> None:
    settings = Settings(benchmark_results_path=tmp_path)
    client = TestClient(create_app(settings, runner_factory=FakeRunner))

    response = client.get("/benchmarks")

    assert response.status_code == 200
    assert response.json() == []
