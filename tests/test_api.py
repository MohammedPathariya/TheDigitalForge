from uuid import UUID

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app
from backend.models import RunResponse, RunStatus
from rag.models import RetrievalEvent, RetrievedSource


class FakeRunner:
    def __init__(self, request: str, settings: Settings):
        self.request = request
        self.settings = settings

    def run(self) -> RunResponse:
        return RunResponse(
            run_id=UUID("00000000-0000-0000-0000-000000000001"),
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
            run_id=UUID("00000000-0000-0000-0000-000000000001"),
            status=RunStatus.completed,
            report="Completed",
            retrieval_events=(RetrievalEvent(query="API usage", results=(source,)),),
        )


def test_health() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_uses_typed_response() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.post("/run", json={"request": "  build a parser  "})

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "00000000-0000-0000-0000-000000000001",
        "status": "completed",
        "report": "Completed: build a parser",
        "retrieval_events": [],
    }


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
