"""Execute one candidate against serialized evaluator cases in a subprocess."""

import importlib.util
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any


def _load_function(candidate_path: Path, function_name: str) -> Any:
    spec = importlib.util.spec_from_file_location("benchmark_candidate", candidate_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load candidate: {candidate_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    function = getattr(module, function_name)
    if not callable(function):
        raise TypeError(f"{function_name} is not callable")
    return function


def main() -> None:
    candidate_path = Path(sys.argv[1])
    function_name = sys.argv[2]
    cases = json.loads(sys.stdin.read())
    passed = 0
    try:
        captured_output = io.StringIO()
        with redirect_stdout(captured_output), redirect_stderr(captured_output):
            function = _load_function(candidate_path, function_name)
        for index, case in enumerate(cases):
            try:
                with redirect_stdout(captured_output), redirect_stderr(captured_output):
                    actual = function(*case["args"])
            except Exception as exc:
                print(
                    json.dumps(
                        {
                            "passed": passed,
                            "error": (
                                f"candidate raised {type(exc).__name__} during "
                                f"hidden case {index}"
                            ),
                        }
                    )
                )
                return
            if actual != case["expected"]:
                print(
                    json.dumps(
                        {
                            "passed": passed,
                            "error": f"hidden case {index} failed",
                        }
                    )
                )
                return
            passed += 1
        print(json.dumps({"passed": passed, "error": None}))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "passed": passed,
                    "error": f"candidate import failed: {type(exc).__name__}",
                }
            )
        )


if __name__ == "__main__":
    main()
