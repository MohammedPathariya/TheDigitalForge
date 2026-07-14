from uuid import UUID

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app
from backend.models import RunResponse, RunStatus


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
    }


def test_run_rejects_blank_request() -> None:
    client = TestClient(create_app(Settings(), runner_factory=FakeRunner))

    response = client.post("/run", json={"request": "   "})

    assert response.status_code == 422


def test_run_rejects_oversized_request() -> None:
    settings = Settings(max_request_characters=3)
    client = TestClient(create_app(settings, runner_factory=FakeRunner))

    response = client.post("/run", json={"request": "four"})

    assert response.status_code == 413
