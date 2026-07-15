import io
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from backend.sandbox import (
    MAX_SANDBOX_OUTPUT_CHARACTERS,
    DockerSandboxRunner,
    ModalSandboxRunner,
    SandboxFile,
    SandboxLimits,
    SandboxRequest,
    SandboxResult,
)
from benchmark.catalog import get_task
from benchmark.evaluator import evaluate_candidate


def _request() -> SandboxRequest:
    return SandboxRequest(
        files=(SandboxFile(path="main.py", content="print('sandboxed')\n"),),
        command=("python", "-B", "/workspace/main.py"),
        limits=SandboxLimits(
            wall_time_seconds=2,
            memory_mib=64,
            cpu_cores=0.5,
            process_limit=8,
        ),
    )


def test_sandbox_result_bounds_captured_output() -> None:
    result = SandboxResult(
        stdout="a" * (MAX_SANDBOX_OUTPUT_CHARACTERS + 1),
        stderr="b" * (MAX_SANDBOX_OUTPUT_CHARACTERS + 1),
        duration_seconds=0.1,
    )

    assert len(result.stdout) == MAX_SANDBOX_OUTPUT_CHARACTERS
    assert len(result.stderr) == MAX_SANDBOX_OUTPUT_CHARACTERS
    assert "<sandbox output truncated>" in result.stdout
    assert result.stdout.startswith("a") and result.stdout.endswith("a")


@pytest.mark.parametrize("path", ["/tmp/x.py", "../x.py", "src/../../x.py"])
def test_sandbox_rejects_files_outside_workspace(path: str) -> None:
    with pytest.raises(ValueError):
        SandboxFile(path=path, content="unsafe")


class CapturingCommandRunner:
    def __init__(self) -> None:
        self.command: list[str] = []
        self.files: dict[str, str] = {}

    def __call__(
        self, command: Sequence[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        self.command = list(command)
        mount = next(part for part in command if part.startswith("--mount="))
        source = mount.split("src=", 1)[1].split(",dst=", 1)[0]
        self.files = {
            path.name: path.read_text(encoding="utf-8")
            for path in Path(source).iterdir()
        }
        return subprocess.CompletedProcess(command, 0, "sandboxed\n", "")


def test_docker_runner_enforces_isolation_and_resource_limits() -> None:
    command_runner = CapturingCommandRunner()
    runner = DockerSandboxRunner(command_runner=command_runner)

    result = runner.run(_request())

    assert result.exit_code == 0
    assert result.stdout == "sandboxed\n"
    assert command_runner.files == {"main.py": "print('sandboxed')\n"}
    assert "--interactive" in command_runner.command
    assert "--network=none" in command_runner.command
    assert "--read-only" in command_runner.command
    assert "--cap-drop=ALL" in command_runner.command
    assert "--security-opt=no-new-privileges" in command_runner.command
    assert "--user=65534:65534" in command_runner.command
    assert "--memory=64m" in command_runner.command
    assert "--memory-swap=64m" in command_runner.command
    assert "--cpus=0.5" in command_runner.command
    assert "--pids-limit=8" in command_runner.command
    assert "timeout" in command_runner.command


class TimingOutCommandRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def __call__(
        self, command: Sequence[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        captured = list(command)
        self.commands.append(captured)
        if captured[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired(captured, kwargs["timeout"])
        return subprocess.CompletedProcess(command, 0, "", "")


def test_docker_runner_force_removes_container_after_host_timeout() -> None:
    command_runner = TimingOutCommandRunner()
    runner = DockerSandboxRunner(command_runner=command_runner)

    result = runner.run(_request())

    container_name = next(
        part.removeprefix("--name=")
        for part in command_runner.commands[0]
        if part.startswith("--name=")
    )
    assert result.timed_out is True
    assert command_runner.commands[1] == [
        "docker",
        "rm",
        "--force",
        container_name,
    ]


class FakeStreamWriter:
    def __init__(self) -> None:
        self.value = ""
        self.eof = False

    def write(self, value: str) -> None:
        self.value += value

    def write_eof(self) -> None:
        self.eof = True

    def drain(self) -> None:
        return None


class FakeProcess:
    def __init__(self) -> None:
        self.stdin = FakeStreamWriter()
        self.stdout = io.StringIO("modal output\n")
        self.stderr = io.StringIO("")

    def wait(self) -> int:
        return 0


class FakeFilesystem:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def make_directory(self, path: str) -> None:
        self.files[path] = "<directory>"

    def write_text(self, content: str, path: str) -> None:
        self.files[path] = content


class FakeSandbox:
    def __init__(self) -> None:
        self.filesystem = FakeFilesystem()
        self.process = FakeProcess()
        self.exec_args: tuple[str, ...] = ()
        self.exec_kwargs: dict[str, Any] = {}
        self.terminated = False
        self.detached = False

    def exec(self, *args: str, **kwargs: Any) -> FakeProcess:
        self.exec_args = args
        self.exec_kwargs = kwargs
        return self.process

    def terminate(self, *, wait: bool) -> None:
        self.terminated = wait

    def detach(self) -> None:
        self.detached = True


class FakeImage:
    def uv_pip_install(self, package: str) -> "FakeImage":
        assert package == "pytest==9.1.1"
        return self


class FakeModal:
    sandbox = FakeSandbox()
    create_kwargs: dict[str, Any] = {}

    class App:
        @staticmethod
        def lookup(name: str, *, create_if_missing: bool) -> str:
            assert name == "digital-forge-sandbox"
            assert create_if_missing is True
            return "app"

    class Image:
        @staticmethod
        def debian_slim(*, python_version: str) -> FakeImage:
            assert python_version == "3.11"
            return FakeImage()

    class Sandbox:
        @staticmethod
        def create(**kwargs: Any) -> FakeSandbox:
            FakeModal.create_kwargs = kwargs
            return FakeModal.sandbox


def test_modal_runner_enforces_limits_and_blocks_network() -> None:
    FakeModal.sandbox = FakeSandbox()
    runner = ModalSandboxRunner(modal_module=FakeModal)

    result = runner.run(_request())

    assert result.exit_code == 0
    assert result.stdout == "modal output\n"
    assert FakeModal.create_kwargs["block_network"] is True
    assert FakeModal.create_kwargs["cpu"] == (0.5, 0.5)
    assert FakeModal.create_kwargs["memory"] == (64, 64)
    assert FakeModal.sandbox.process.stdin.eof is True
    assert FakeModal.sandbox.terminated is True
    assert FakeModal.sandbox.detached is True
    assert "/workspace/main.py" in FakeModal.sandbox.filesystem.files
    assert "8" in FakeModal.sandbox.exec_args


@pytest.mark.skipif(
    not DockerSandboxRunner.available(), reason="Docker daemon is unavailable"
)
def test_docker_runner_smoke() -> None:
    result = DockerSandboxRunner().run(_request())

    assert result.exit_code == 0, result.stderr or result.error
    assert result.stdout == "sandboxed\n"


@pytest.mark.skipif(
    not DockerSandboxRunner.available(), reason="Docker daemon is unavailable"
)
def test_benchmark_evaluator_docker_smoke(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "def dedupe_crates(crate_ids):\n    return list(dict.fromkeys(crate_ids))\n",
        encoding="utf-8",
    )

    result = evaluate_candidate(get_task("forge_easy_02"), candidate)

    assert result.passed is True, result.error
