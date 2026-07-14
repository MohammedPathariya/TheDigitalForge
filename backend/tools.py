"""Workspace and CrewAI tools scoped to one pipeline run."""

from collections.abc import Sequence
from pathlib import Path

from crewai.tools import BaseTool, tool

from .sandbox import (
    DockerSandboxRunner,
    SandboxFile,
    SandboxLimits,
    SandboxRequest,
    SandboxRunner,
)
from .workspace import RunWorkspace


def build_file_system_tools(
    workspace: RunWorkspace,
    sandbox_runner: SandboxRunner | None = None,
    *,
    timeout_seconds: float = 10.0,
    memory_mib: int = 256,
    cpu_cores: float = 1.0,
    process_limit: int = 64,
) -> Sequence[BaseTool]:
    """Bind file operations to a single run workspace."""

    runner = sandbox_runner or DockerSandboxRunner()
    limits = SandboxLimits(
        wall_time_seconds=timeout_seconds,
        memory_mib=memory_mib,
        cpu_cores=cpu_cores,
        process_limit=process_limit,
    )

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

        result = runner.run(
            SandboxRequest(
                files=(
                    SandboxFile(path=code_file_path, content=code_content),
                    SandboxFile(path=normalized_test_path, content=test_content),
                ),
                command=(
                    "python",
                    "-B",
                    "-m",
                    "pytest",
                    f"/workspace/{normalized_test_path}",
                    "--maxfail=1",
                    "--disable-warnings",
                    "-p",
                    "no:cacheprovider",
                    "-q",
                ),
                limits=limits,
            )
        )
        if result.timed_out:
            return "TESTS FAILED:\nSandbox execution timed out."
        if result.error:
            return f"TESTS FAILED:\nSandbox infrastructure error: {result.error}"
        if result.exit_code == 0:
            return "ALL TESTS PASSED"
        return (
            f"TESTS FAILED:\n--- STDOUT ---\n{result.stdout}\n"
            f"--- STDERR ---\n{result.stderr}"
        ).strip()

    return [save_file, run_tests]
