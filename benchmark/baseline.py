"""Zero-shot benchmark runner and OpenAI model adapter."""

import argparse
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from openai import OpenAI

from backend.sandbox import (
    DockerSandboxRunner,
    ModalSandboxRunner,
    SandboxRunner,
)

from .catalog import BENCHMARK_VERSION, get_task, load_tasks
from .evaluator import evaluate_candidate
from .hidden_cases import evaluator_sha256
from .models import (
    BenchmarkReport,
    BenchmarkTask,
    GeneratedSolution,
    TaskResult,
    utc_now,
)

BASELINE_INSTRUCTIONS = (
    "Solve the algorithm task in Python 3. Return only executable Python code that "
    "defines the requested function. Do not include markdown fences, tests, or prose."
)


class SolutionGenerator(Protocol):
    def generate(self, task: BenchmarkTask, model: str) -> GeneratedSolution: ...


class OpenAISolutionGenerator:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI()

    def generate(self, task: BenchmarkTask, model: str) -> GeneratedSolution:
        response = self.client.responses.create(
            model=model,
            instructions=BASELINE_INSTRUCTIONS,
            input=task.prompt,
            store=False,
        )
        usage = response.usage
        return GeneratedSolution(
            code=_extract_code(response.output_text),
            response_id=response.id,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
        )


def _extract_code(raw: str) -> str:
    text = raw.strip()
    match = re.fullmatch(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    code = match.group(1).strip() if match else text
    if not code:
        raise ValueError("Model returned an empty candidate.")
    return code + "\n"


class ZeroShotBaselineRunner:
    def __init__(
        self,
        generator: SolutionGenerator,
        model: str,
        output_root: Path,
        sandbox_runner: SandboxRunner | None = None,
    ):
        self.generator = generator
        self.model = model
        self.output_root = output_root
        self.sandbox_runner = sandbox_runner or DockerSandboxRunner()

    def run(self, tasks: Sequence[BenchmarkTask] | None = None) -> BenchmarkReport:
        selected = tuple(tasks or load_tasks())
        run_id = uuid4().hex
        run_directory = self.output_root / run_id
        candidates_directory = run_directory / "candidates"
        candidates_directory.mkdir(parents=True, exist_ok=False)
        started_at = utc_now()
        results = tuple(self._run_task(task, candidates_directory) for task in selected)
        report = BenchmarkReport(
            benchmark_version=BENCHMARK_VERSION,
            evaluator_sha256=evaluator_sha256(),
            run_id=run_id,
            model=self.model,
            sandbox_backend=self.sandbox_runner.name,
            started_at=started_at,
            completed_at=utc_now(),
            tasks_passed=sum(result.passed for result in results),
            tasks_total=len(results),
            results=results,
        )
        report.write(run_directory / "report.json")
        return report

    def _run_task(self, task: BenchmarkTask, directory: Path) -> TaskResult:
        candidate_path = directory / f"{task.id}.py"
        try:
            generated = self.generator.generate(task, self.model)
            candidate_path.write_text(generated.code, encoding="utf-8")
            evaluation = evaluate_candidate(task, candidate_path, self.sandbox_runner)
            return TaskResult(
                task_id=task.id,
                task_version=task.version,
                difficulty=task.difficulty,
                passed=evaluation.passed,
                tests_passed=evaluation.tests_passed,
                tests_total=evaluation.tests_total,
                duration_seconds=evaluation.duration_seconds,
                candidate_path=str(candidate_path),
                response_id=generated.response_id,
                input_tokens=generated.input_tokens,
                output_tokens=generated.output_tokens,
                error=evaluation.error,
            )
        except Exception as exc:
            return TaskResult(
                task_id=task.id,
                task_version=task.version,
                difficulty=task.difficulty,
                passed=False,
                tests_passed=0,
                tests_total=0,
                duration_seconds=0,
                candidate_path=str(candidate_path),
                error=f"generation failed: {type(exc).__name__}: {exc}",
            )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the zero-shot benchmark baseline")
    parser.add_argument(
        "--model", required=True, help="Exact OpenAI model ID to record"
    )
    parser.add_argument(
        "--task",
        action="append",
        dest="task_ids",
        help="Task ID to run; repeat to select multiple tasks (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-results"),
        help="Directory for candidates and report artifacts",
    )
    parser.add_argument(
        "--sandbox",
        choices=("docker", "modal"),
        default="docker",
        help="Isolated execution backend (default: docker)",
    )
    parser.add_argument(
        "--modal-app",
        default="digital-forge-sandbox",
        help="Modal app used when --sandbox=modal",
    )
    args = parser.parse_args(argv)
    tasks = [get_task(task_id) for task_id in args.task_ids] if args.task_ids else None
    sandbox_runner: SandboxRunner = (
        ModalSandboxRunner(args.modal_app)
        if args.sandbox == "modal"
        else DockerSandboxRunner()
    )
    report = ZeroShotBaselineRunner(
        OpenAISolutionGenerator(), args.model, args.output, sandbox_runner
    ).run(tasks)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
