from types import SimpleNamespace
from uuid import UUID

import pytest

from backend.config import Settings
from benchmark.catalog import get_task
from benchmark.digital_forge import DigitalForgeSolutionGenerator


class FakeWorkspace:
    def read(self, path: str) -> str | None:
        if path == "solution.py":
            return "def dedupe_crates(crate_ids):\n    return list(dict.fromkeys(crate_ids))\n"
        return None


class FakeDevelopmentCrew:
    def __init__(self, request: str, settings: Settings):
        self.request = request
        self.settings = settings
        self.state = SimpleNamespace(
            plan=SimpleNamespace(file_name="solution.py"),
            workspace=FakeWorkspace(),
        )

    def run(self) -> SimpleNamespace:
        return SimpleNamespace(run_id=UUID("12345678-1234-5678-1234-567812345678"))


def test_digital_forge_generator_returns_final_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("benchmark.digital_forge.DevelopmentCrew", FakeDevelopmentCrew)
    settings = Settings(openai_api_key="test-key", openai_model_name="gpt-4")
    task = get_task("forge_easy_02")

    generated = DigitalForgeSolutionGenerator(settings).generate(
        task, "digital-forge:gpt-4"
    )

    assert generated.code.startswith("def dedupe_crates")
    assert generated.response_id == "12345678-1234-5678-1234-567812345678"
