import json
from pathlib import Path
from typing import Any

from backend.sandbox import SandboxRequest, SandboxResult
from benchmark.catalog import get_task
from benchmark.evaluator import evaluate_candidate
from benchmark.hidden_cases import HIDDEN_CASES, to_jsonable


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
    return [to_jsonable(case.expected) for case in HIDDEN_CASES[task_id]]


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
        to_jsonable(case.args) for case in HIDDEN_CASES[task.id]
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


def test_correct_slug_reference_matches_all_hidden_cases(tmp_path: Path) -> None:
    task = get_task("forge_easy_08")
    values = []
    for case in HIDDEN_CASES[task.id]:
        title, existing = to_jsonable(case.args)
        slug = []
        in_separator = False
        for character in title.lower():
            if character.isascii() and character.isalnum():
                slug.append(character)
                in_separator = False
            elif slug and not in_separator:
                slug.append("-")
                in_separator = True
        base = "".join(slug).strip("-") or "item"
        candidate = base
        suffix = 2
        while candidate in existing:
            candidate = f"{base}-{suffix}"
            suffix += 1
        values.append(candidate)

    result = evaluate_candidate(
        task, _candidate(tmp_path), StubSandboxRunner(_outputs(values))
    )

    assert result.passed is True


def test_correct_deployment_order_reference_matches_all_hidden_cases(
    tmp_path: Path,
) -> None:
    task = get_task("forge_medium_05")
    values = []
    for case in HIDDEN_CASES[task.id]:
        services, dependencies = to_jsonable(case.args)
        service_set = set(services)
        outgoing: dict[str, set[str]] = {service: set() for service in service_set}
        incoming = {service: 0 for service in service_set}
        for before, after in dependencies:
            if before not in service_set or after not in service_set:
                continue
            if after not in outgoing[before]:
                outgoing[before].add(after)
                incoming[after] += 1
        available = sorted(service for service, count in incoming.items() if count == 0)
        order = []
        while available:
            current = available.pop(0)
            order.append(current)
            for after in sorted(outgoing[current]):
                incoming[after] -= 1
                if incoming[after] == 0:
                    available.append(after)
                    available.sort()
        values.append(order if len(order) == len(service_set) else [])

    result = evaluate_candidate(
        task, _candidate(tmp_path), StubSandboxRunner(_outputs(values))
    )

    assert result.passed is True
