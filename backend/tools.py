"""Workspace and CrewAI tools scoped to one pipeline run."""

import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from crewai.tools import BaseTool, tool

from .workspace import RunWorkspace


def build_file_system_tools(workspace: RunWorkspace) -> Sequence[BaseTool]:
    """Bind file operations to a single run workspace."""

    @tool("save_file")
    def save_file(file_path: str, content: str) -> str:
        """Save text to a relative file path in this run's isolated workspace."""
        normalized = workspace.write(file_path, content)
        return f"File '{normalized}' saved in memory."

    @tool("run_tests")
    def run_tests(test_file_path: str) -> str:
        """Run a generated pytest suite against code from this run's workspace."""
        try:
            normalized_test_path = workspace.normalize(test_file_path)
        except ValueError as exc:
            return f"Error: {exc}"

        test_name = Path(normalized_test_path).name
        if not test_name.startswith("test_"):
            return "Error: Test file name must start with 'test_'."

        code_name = test_name.removeprefix("test_")
        code_file_path = str(Path(normalized_test_path).with_name(code_name))
        code_content = workspace.read(code_file_path)
        test_content = workspace.read(normalized_test_path)
        if code_content is None:
            return f"Error: Code file '{code_file_path}' not found in memory."
        if test_content is None:
            return f"Error: Test file '{normalized_test_path}' not found in memory."

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_code_file = temp_dir_path / code_file_path
            temp_test_file = temp_dir_path / normalized_test_path
            temp_code_file.parent.mkdir(parents=True, exist_ok=True)
            temp_test_file.parent.mkdir(parents=True, exist_ok=True)
            temp_code_file.write_text(code_content, encoding="utf-8")
            temp_test_file.write_text(test_content, encoding="utf-8")

            command = [
                sys.executable,
                "-m",
                "pytest",
                str(temp_test_file),
                "--maxfail=1",
                "--disable-warnings",
                "-q",
            ]
            try:
                subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=temp_dir_path,
                )
                return "ALL TESTS PASSED"
            except subprocess.CalledProcessError as exc:
                return (
                    f"TESTS FAILED:\n--- STDOUT ---\n{exc.stdout}\n"
                    f"--- STDERR ---\n{exc.stderr}"
                ).strip()

    return [save_file, run_tests]
