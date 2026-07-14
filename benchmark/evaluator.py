"""Local hidden-test evaluator used until sandbox adapters arrive on Day 3."""

import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .hidden_cases import HIDDEN_CASES
from .models import BenchmarkTask, EvaluationResult


def evaluate_candidate(task: BenchmarkTask, candidate_path: Path) -> EvaluationResult:
    cases = HIDDEN_CASES[task.id]
    payload = json.dumps([asdict(case) for case in cases])
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "benchmark._worker",
                str(candidate_path.resolve()),
                task.function_name,
            ],
            input=payload,
            capture_output=True,
            text=True,
            timeout=task.time_limit_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=time.monotonic() - started,
            error=f"candidate exceeded {task.time_limit_seconds:.1f}s time limit",
        )

    duration = time.monotonic() - started
    if completed.returncode != 0:
        error = completed.stderr.strip() or f"worker exited with {completed.returncode}"
        return EvaluationResult(
            passed=False,
            tests_passed=0,
            tests_total=len(cases),
            duration_seconds=duration,
            error=error,
        )
    try:
        outcome = json.loads(completed.stdout)
        tests_passed = int(outcome["passed"])
        error = outcome["error"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        tests_passed = 0
        error = "candidate produced invalid evaluator output"
    return EvaluationResult(
        passed=tests_passed == len(cases) and error is None,
        tests_passed=tests_passed,
        tests_total=len(cases),
        duration_seconds=duration,
        error=error,
    )
