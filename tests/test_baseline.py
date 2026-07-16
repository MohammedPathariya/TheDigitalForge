import json
from pathlib import Path
from typing import Any

from backend.sandbox import SandboxRequest, SandboxResult
from benchmark.baseline import SolutionGenerator, ZeroShotBaselineRunner, _extract_code
from benchmark.catalog import get_task
from benchmark.hidden_cases import HIDDEN_CASES, to_jsonable
from benchmark.models import BenchmarkTask, GeneratedSolution


class RecordingGenerator(SolutionGenerator):
    def __init__(self) -> None:
        self.received_prompts: list[str] = []

    def generate(self, task: BenchmarkTask, model: str) -> GeneratedSolution:
        self.received_prompts.append(task.prompt)
        return GeneratedSolution(
            code="def dedupe_crates(crate_ids):\n    return list(dict.fromkeys(crate_ids))\n",
            response_id="response-test",
            input_tokens=10,
            output_tokens=20,
        )


class PassingSandboxRunner:
    name = "stub"

    def run(self, request: SandboxRequest) -> SandboxResult:
        task = get_task("forge_easy_02")
        results: list[dict[str, Any]] = [
            {
                "value": to_jsonable(case.expected),
                "error_type": None,
            }
            for case in HIDDEN_CASES[task.id]
        ]
        return SandboxResult(
            stdout=json.dumps({"results": results, "import_error": None}),
            exit_code=0,
            duration_seconds=0.01,
        )


def test_zero_shot_runner_writes_structured_artifacts_without_exposing_cases(
    tmp_path: Path,
) -> None:
    generator = RecordingGenerator()
    task = get_task("forge_easy_02")

    report = ZeroShotBaselineRunner(
        generator, "test-model", tmp_path, PassingSandboxRunner()
    ).run([task])

    report_path = tmp_path / report.run_id / "report.json"
    artifact = json.loads(report_path.read_text(encoding="utf-8"))
    assert report.tasks_passed == 1
    assert artifact["schema_version"] == "1.1.0"
    assert artifact["benchmark_version"] == "1.1.0"
    assert artifact["model"] == "test-model"
    assert artifact["sandbox_backend"] == "stub"
    assert artifact["results"][0]["response_id"] == "response-test"
    assert generator.received_prompts == [task.prompt]
    assert "same" not in generator.received_prompts[0]


def test_extract_code_accepts_plain_or_fenced_python() -> None:
    assert _extract_code("def solve():\n    pass") == "def solve():\n    pass\n"
    assert _extract_code("```python\ndef solve():\n    pass\n```") == (
        "def solve():\n    pass\n"
    )
