"""Execute candidate inputs without access to hidden expected outputs."""

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
    inputs = json.loads(sys.stdin.read())
    results: list[dict[str, Any]] = []
    try:
        captured_output = io.StringIO()
        with redirect_stdout(captured_output), redirect_stderr(captured_output):
            function = _load_function(candidate_path, function_name)
        for args in inputs:
            try:
                with redirect_stdout(captured_output), redirect_stderr(captured_output):
                    value = function(*args)
            except Exception as exc:
                results.append({"value": None, "error_type": type(exc).__name__})
                break
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                results.append({"value": None, "error_type": "SerializationError"})
                break
            results.append({"value": value, "error_type": None})
        print(json.dumps({"results": results, "import_error": None}))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "results": results,
                    "import_error": type(exc).__name__,
                }
            )
        )


if __name__ == "__main__":
    main()
