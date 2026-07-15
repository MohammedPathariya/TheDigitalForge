import json
from pathlib import Path
from typing import Any

from backend.sandbox import SandboxRequest, SandboxResult
from benchmark.catalog import get_task
from benchmark.evaluator import evaluate_candidate
from benchmark.hidden_cases import HIDDEN_CASES


class StubSandboxRunner:
    name = "stub"

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.request: SandboxRequest | None = None

    def run(self, request: SandboxRequest) -> SandboxResult:
        self.request = request
        return SandboxResult(
            stdout=json.dumps(self.payload),
            exit_code=0,
            duration_seconds=0.01,
        )


def _outputs(values: list[Any]) -> dict[str, Any]:
    return {
        "results": [{"value": value, "error_type": None} for value in values],
        "import_error": None,
    }


def _expected(task_id: str) -> list[Any]:
    return [json.loads(json.dumps(case.expected)) for case in HIDDEN_CASES[task_id]]


def _candidate(tmp_path: Path, code: str = "def solution(): pass\n") -> Path:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(code, encoding="utf-8")
    return candidate


def test_evaluator_accepts_correct_candidate_without_copying_expected_outputs(
    tmp_path: Path,
) -> None:
    task = get_task("forge_easy_02")
    runner = StubSandboxRunner(_outputs(_expected(task.id)))

    result = evaluate_candidate(task, _candidate(tmp_path), runner)

    assert result.passed is True
    assert result.tests_passed == result.tests_total
    assert runner.request is not None
    sandbox_files = "\n".join(file.content for file in runner.request.files)
    assert "HIDDEN_CASES" not in sandbox_files
    assert json.loads(runner.request.stdin) == [
        json.loads(json.dumps(case.args)) for case in HIDDEN_CASES[task.id]
    ]


def test_evaluator_reports_hidden_failure_without_revealing_values(
    tmp_path: Path,
) -> None:
    task = get_task("forge_easy_02")
    values = _expected(task.id)
    values[1] = []

    result = evaluate_candidate(
        task, _candidate(tmp_path), StubSandboxRunner(_outputs(values))
    )

    assert result.passed is False
    assert result.tests_passed == 1
    assert result.error == "hidden case failed during hidden case 1"
    assert "expected" not in result.error


def test_evaluator_sanitizes_candidate_exceptions(tmp_path: Path) -> None:
    runner = StubSandboxRunner(
        {
            "results": [{"value": None, "error_type": "ValueError"}],
            "import_error": None,
        }
    )

    result = evaluate_candidate(get_task("forge_easy_02"), _candidate(tmp_path), runner)

    assert result.error == "candidate raised ValueError during hidden case 0"


def test_correct_palindrome_reference_matches_all_hidden_cases(tmp_path: Path) -> None:
    task = get_task("forge_easy_09")
    values = []
    for case in HIDDEN_CASES[task.id]:
        text = case.args[0]
        normalized = "".join(
            character.lower()
            for character in text
            if character.isascii() and character.isalnum()
        )
        values.append(normalized == normalized[::-1])

    result = evaluate_candidate(
        task, _candidate(tmp_path), StubSandboxRunner(_outputs(values))
    )

    assert result.passed is True


def test_correct_budget_pair_reference_matches_all_hidden_cases(tmp_path: Path) -> None:
    task = get_task("forge_medium_09")
    values = []
    for case in HIDDEN_CASES[task.id]:
        costs, budget = case.args
        ranked = (
            (abs(costs[i] + costs[j] - budget), i, j)
            for i in range(len(costs))
            for j in range(i + 1, len(costs))
        )
        values.append(list(min(ranked)[1:]))

    result = evaluate_candidate(
        task, _candidate(tmp_path), StubSandboxRunner(_outputs(values))
    )

    assert result.passed is True
