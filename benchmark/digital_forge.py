"""Digital Forge adapter for the algorithm benchmark."""

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

from backend.config import Settings
from backend.pipeline import DevelopmentCrew
from backend.sandbox import DockerSandboxRunner, ModalSandboxRunner, SandboxRunner

from .baseline import ZeroShotBaselineRunner, _extract_code
from .catalog import get_task
from .models import BenchmarkTask, GeneratedSolution


class DigitalForgeSolutionGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, task: BenchmarkTask, model: str) -> GeneratedSolution:
        expected_label = f"digital-forge:{self.settings.openai_model_name}"
        if model != expected_label:
            raise ValueError(f"Expected benchmark model label {expected_label!r}.")

        crew = DevelopmentCrew(task.prompt, self.settings)
        response = crew.run()
        plan = crew.state.plan
        if plan is None:
            raise ValueError("Digital Forge did not produce a development plan.")
        code = crew.state.workspace.read(plan.file_name)
        if not code:
            raise ValueError("Digital Forge did not produce application code.")
        return GeneratedSolution(
            code=_extract_code(code),
            response_id=str(response.run_id),
        )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Digital Forge benchmark")
    parser.add_argument(
        "--model",
        help="Exact OpenAI model ID (default: OPENAI_MODEL_NAME or gpt-4)",
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
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=None,
        help="Stop early after this many consecutive failures (default: disabled)",
    )
    parser.add_argument(
        "--finish-remaining-threshold",
        type=int,
        default=3,
        help="Ignore the failure guard when this many or fewer tasks remain",
    )
    args = parser.parse_args(argv)

    runtime_directory = (args.output / ".runtime").resolve()
    runtime_directory.mkdir(parents=True, exist_ok=True)
    crewai_storage_directory = runtime_directory / "crewai"
    crewai_storage_directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CREWAI_STORAGE_DIR", str(crewai_storage_directory))
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")

    base_settings = Settings()
    model_name = args.model or base_settings.openai_model_name
    settings = base_settings.model_copy(
        update={
            "openai_model_name": model_name,
            "sandbox_backend": args.sandbox,
            "modal_sandbox_app": args.modal_app,
        }
    )
    tasks = [get_task(task_id) for task_id in args.task_ids] if args.task_ids else None
    sandbox_runner: SandboxRunner = (
        ModalSandboxRunner(args.modal_app)
        if args.sandbox == "modal"
        else DockerSandboxRunner(settings.docker_sandbox_image)
    )
    label = f"digital-forge:{model_name}"
    report = ZeroShotBaselineRunner(
        DigitalForgeSolutionGenerator(settings),
        label,
        args.output,
        sandbox_runner,
        max_consecutive_failures=args.max_consecutive_failures,
        finish_remaining_threshold=args.finish_remaining_threshold,
    ).run(tasks)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
