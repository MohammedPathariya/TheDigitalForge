from backend.sandbox import SandboxRequest, SandboxResult
from backend.tools import build_file_system_tools
from backend.workspace import RunWorkspace


class PassingSandboxRunner:
    name = "stub"

    def __init__(self) -> None:
        self.request: SandboxRequest | None = None

    def run(self, request: SandboxRequest) -> SandboxResult:
        self.request = request
        return SandboxResult(exit_code=0, duration_seconds=0.01)


class CleanupFailingSandboxRunner:
    name = "stub"

    def run(self, request: SandboxRequest) -> SandboxResult:
        return SandboxResult(
            exit_code=0,
            duration_seconds=0.01,
            error="Sandbox cleanup failed.",
        )


def test_generated_tests_run_through_sandbox() -> None:
    workspace = RunWorkspace()
    workspace.write("solution.py", "def answer(): return 42\n")
    workspace.write(
        "test_solution.py",
        "from solution import answer\n\ndef test_answer(): assert answer() == 42\n",
    )
    runner = PassingSandboxRunner()
    tools = build_file_system_tools(workspace, runner)
    run_tests = next(tool for tool in tools if tool.name == "run_tests")

    result = run_tests.run(test_file_path="test_solution.py")

    assert result == "ALL TESTS PASSED"
    assert runner.request is not None
    assert {file.path for file in runner.request.files} == {
        "solution.py",
        "test_solution.py",
    }
    assert runner.request.command[:4] == ("python", "-B", "-m", "pytest")


def test_sandbox_cleanup_failure_is_not_reported_as_success() -> None:
    workspace = RunWorkspace()
    workspace.write("solution.py", "def answer(): return 42\n")
    workspace.write("test_solution.py", "def test_answer(): assert True\n")
    tools = build_file_system_tools(workspace, CleanupFailingSandboxRunner())
    run_tests = next(tool for tool in tools if tool.name == "run_tests")

    result = run_tests.run(test_file_path="test_solution.py")

    assert "FAILURE CLASS: infrastructure" in result
    assert "RESPONSIBLE AGENT: system" in result


def test_save_file_rejects_invalid_python_without_overwriting_workspace() -> None:
    workspace = RunWorkspace()
    workspace.write("solution.py", "def answer():\n    return 1\n")
    save_file = next(
        tool for tool in build_file_system_tools(workspace) if tool.name == "save_file"
    )

    result = save_file.run(
        file_path="solution.py", content="def answer():\n    return 1}\n"
    )

    assert "syntax validation failed" in result
    assert workspace.read("solution.py") == "def answer():\n    return 1\n"
