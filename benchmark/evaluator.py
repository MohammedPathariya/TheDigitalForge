"""Host-side hidden-test evaluation backed by an isolated sandbox."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.sandbox import (
    DockerSandboxRunner,
    SandboxFile,
    SandboxLimits,
    SandboxRequest,
    SandboxRunner,
)

from .hidden_cases import HIDDEN_CASES, to_jsonable
from .models import BenchmarkTask, EvaluationResult

WORKER_PATH = Path(__file__).with_name("_worker.py")


class _CaseOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: Any = None
    error_type: str | None = None


class _WorkerOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    results: tuple[_CaseOutput, ...]
    import_error: str | None = None


def evaluate_candidate(
    task: BenchmarkTask,
    candidate_path: Path,
    sandbox_runner: SandboxRunner | None = None,
) -> EvaluationResult:
    cases = HIDDEN_CASES[task.id]
    runner = sandbox_runner or DockerSandboxRunner()
    execution = runner.run(
        SandboxRequest(
            files=(
                SandboxFile(
                    path="candidate.py",
                    content=candidate_path.read_text(encoding="utf-8"),
                ),
                SandboxFile(
                    path="worker.py",
                    content=WORKER_PATH.read_text(encoding="utf-8"),
                ),
            ),
            command=(
                "python",
                "-I",
                "-B",
                "/workspace/worker.py",
                "/workspace/candidate.py",
                task.function_name,
            ),
            stdin=json.dumps([to_jsonable(case.args) for case in cases]),
            limits=SandboxLimits(wall_time_seconds=task.time_limit_seconds),
        )
    )
    if execution.timed_out:
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=execution.duration_seconds,
            error=f"candidate exceeded {task.time_limit_seconds:.1f}s time limit",
        )
    if execution.error:
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=execution.duration_seconds,
            error=f"sandbox infrastructure error: {execution.error}",
        )
    if execution.exit_code != 0:
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=execution.duration_seconds,
            error=f"sandbox worker exited with {execution.exit_code}",
        )
    try:
        output = _WorkerOutput.model_validate_json(execution.stdout)
    except ValueError:
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=execution.duration_seconds,
            error="candidate produced invalid evaluator output",
        )
    if output.import_error:
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=execution.duration_seconds,
            error=f"candidate import failed: {output.import_error}",
        )
    for index, (case, result) in enumerate(zip(cases, output.results, strict=False)):
        if result.error_type:
            return _failed_result(
                cases,
                execution.duration_seconds,
                index,
                f"candidate raised {result.error_type}",
            )
        expected = to_jsonable(case.expected)
        if result.value != expected:
            return _failed_result(
                cases, execution.duration_seconds, index, "hidden case failed"
            )
    if len(output.results) != len(cases):
        return EvaluationResult(
            passed=False,
            tests_passed=len(output.results),
            tests_total=len(cases),
            duration_seconds=execution.duration_seconds,
            error="candidate returned incomplete evaluator output",
        )
    return EvaluationResult(
        passed=True,
        tests_passed=len(cases),
        tests_total=len(cases),
        duration_seconds=execution.duration_seconds,
    )


def _failed_result(
    cases: tuple[Any, ...],
    duration_seconds: float,
    index: int,
    reason: str,
) -> EvaluationResult:
    return EvaluationResult(
        passed=False,
        tests_passed=index,
        tests_total=len(cases),
        duration_seconds=duration_seconds,
        error=f"{reason} during hidden case {index}",
    )
