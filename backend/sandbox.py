"""Isolated command execution through Docker or Modal Sandboxes."""

import importlib
import json
import math
import subprocess
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .sandbox_dependencies import SANDBOX_PACKAGES

DEFAULT_DOCKER_IMAGE = "digital-forge-sandbox:py311"
DEFAULT_MODAL_APP = "digital-forge-sandbox"
MAX_SANDBOX_OUTPUT_CHARACTERS = 32_000
SANDBOX_ROOT = PurePosixPath("/workspace")


class SandboxLimits(BaseModel):
    model_config = ConfigDict(frozen=True)

    wall_time_seconds: float = Field(default=5.0, gt=0, le=60)
    memory_mib: int = Field(default=256, ge=32, le=1024)
    cpu_cores: float = Field(default=1.0, ge=0.1, le=2.0)
    process_limit: int = Field(default=64, ge=4, le=128)


class SandboxFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    content: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise ValueError("Sandbox file paths must stay inside the workspace.")
        if "\\" in value or path == PurePosixPath("."):
            raise ValueError("Sandbox file paths must use relative POSIX syntax.")
        return str(path)


class SandboxRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    files: tuple[SandboxFile, ...]
    command: tuple[str, ...] = Field(min_length=1)
    stdin: str = ""
    limits: SandboxLimits = Field(default_factory=SandboxLimits)

    @model_validator(mode="after")
    def validate_unique_files(self) -> "SandboxRequest":
        paths = [file.path for file in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("Sandbox file paths must be unique.")
        return self


class SandboxResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_seconds: float = Field(ge=0)
    timed_out: bool = False
    error: str | None = None

    @field_validator("stdout", "stderr")
    @classmethod
    def bound_output(cls, value: str) -> str:
        if len(value) <= MAX_SANDBOX_OUTPUT_CHARACTERS:
            return value
        marker = "\n... <sandbox output truncated>\n"
        available = MAX_SANDBOX_OUTPUT_CHARACTERS - len(marker)
        head = available // 2
        tail = available - head
        return f"{value[:head]}{marker}{value[-tail:]}"


class SandboxRunner(Protocol):
    name: str

    def run(self, request: SandboxRequest) -> SandboxResult: ...


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def _run_command(
    command: Sequence[str], **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, **kwargs)


class DockerSandboxRunner:
    name = "docker"

    def __init__(
        self,
        image: str = DEFAULT_DOCKER_IMAGE,
        command_runner: CommandRunner = _run_command,
    ):
        self.image = image
        self._command_runner = command_runner

    @staticmethod
    def available() -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def run(self, request: SandboxRequest) -> SandboxResult:
        started = time.monotonic()
        container_name = f"digital-forge-{uuid4().hex}"
        try:
            with tempfile.TemporaryDirectory(prefix="digital-forge-sandbox-") as root:
                root_path = Path(root)
                self._write_files(root_path, request.files)
                command = self._docker_command(root_path, request, container_name)
                completed = self._command_runner(
                    command,
                    input=request.stdin,
                    capture_output=True,
                    text=True,
                    timeout=request.limits.wall_time_seconds + 15,
                    check=False,
                )
        except subprocess.TimeoutExpired as exc:
            cleanup_error = self._force_remove(container_name)
            timeout_error = "Docker sandbox exceeded its host timeout."
            if cleanup_error:
                timeout_error = f"{timeout_error} {cleanup_error}"
            return SandboxResult(
                stdout=_stream_text(exc.stdout),
                stderr=_stream_text(exc.stderr),
                duration_seconds=time.monotonic() - started,
                timed_out=True,
                error=timeout_error,
            )
        except FileNotFoundError:
            return SandboxResult(
                duration_seconds=time.monotonic() - started,
                error="Docker CLI is not installed or not on PATH.",
            )
        except OSError as exc:
            return SandboxResult(
                duration_seconds=time.monotonic() - started,
                error=f"Docker sandbox could not start: {type(exc).__name__}.",
            )

        timed_out = completed.returncode == 124
        error = None
        if completed.returncode == 125:
            error = "Docker could not create the sandbox container."
        return SandboxResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            duration_seconds=time.monotonic() - started,
            timed_out=timed_out,
            error=error,
        )

    def _docker_command(
        self, root: Path, request: SandboxRequest, container_name: str
    ) -> list[str]:
        limits = request.limits
        return [
            "docker",
            "run",
            "--rm",
            "--interactive",
            f"--name={container_name}",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=65534:65534",
            f"--memory={limits.memory_mib}m",
            f"--memory-swap={limits.memory_mib}m",
            f"--cpus={limits.cpu_cores}",
            f"--pids-limit={limits.process_limit}",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--env=HOME=/tmp",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            f"--mount=type=bind,src={root},dst={SANDBOX_ROOT},readonly",
            f"--workdir={SANDBOX_ROOT}",
            self.image,
            "timeout",
            "--signal=TERM",
            "--kill-after=1s",
            f"{limits.wall_time_seconds}s",
            *request.command,
        ]

    def _force_remove(self, container_name: str) -> str | None:
        try:
            completed = self._command_runner(
                ["docker", "rm", "--force", container_name],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
            return f"Forced container cleanup failed: {type(exc).__name__}."
        if completed.returncode == 0 or "No such container" in completed.stderr:
            return None
        return "Forced container cleanup failed."

    @staticmethod
    def _write_files(root: Path, files: tuple[SandboxFile, ...]) -> None:
        root.chmod(0o755)
        for file in files:
            destination = root / file.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.parent.chmod(0o755)
            destination.write_text(file.content, encoding="utf-8")
            destination.chmod(0o444)


_MODAL_LAUNCHER = """\
import json
import os
import resource
import sys

limit = int(sys.argv[1])
resource.setrlimit(resource.RLIMIT_NPROC, (limit, limit))
if os.geteuid() == 0:
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
command = json.loads(sys.argv[2])
os.execvp(command[0], command)
"""


class ModalSandboxRunner:
    name = "modal"

    def __init__(
        self,
        app_name: str = DEFAULT_MODAL_APP,
        modal_module: Any | None = None,
    ):
        self.app_name = app_name
        self._modal = modal_module

    def run(self, request: SandboxRequest) -> SandboxResult:
        started = time.monotonic()
        sandbox: Any | None = None
        try:
            modal = self._modal or importlib.import_module("modal")
            app = modal.App.lookup(self.app_name, create_if_missing=True)
            image = modal.Image.debian_slim(python_version="3.11").uv_pip_install(
                *SANDBOX_PACKAGES
            )
            limits = request.limits
            sandbox = modal.Sandbox.create(
                app=app,
                image=image,
                timeout=max(60, math.ceil(limits.wall_time_seconds) + 30),
                cpu=(limits.cpu_cores, limits.cpu_cores),
                memory=(limits.memory_mib, limits.memory_mib),
                block_network=True,
                workdir="/tmp",
            )
            sandbox.filesystem.make_directory(str(SANDBOX_ROOT))
            for file in request.files:
                sandbox.filesystem.write_text(
                    file.content, str(SANDBOX_ROOT / file.path)
                )
            launcher_path = "/tmp/digital_forge_launcher.py"
            sandbox.filesystem.write_text(_MODAL_LAUNCHER, launcher_path)
            process = sandbox.exec(
                "python",
                "-I",
                "-B",
                launcher_path,
                str(limits.process_limit),
                json.dumps(request.command),
                timeout=max(1, math.ceil(limits.wall_time_seconds)),
                workdir=str(SANDBOX_ROOT),
                env={"HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"},
            )
            if request.stdin:
                process.stdin.write(request.stdin)
            process.stdin.write_eof()
            process.stdin.drain()
            stdout = process.stdout.read()
            stderr = process.stderr.read()
            exit_code = process.wait()
            result = SandboxResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_seconds=time.monotonic() - started,
            )
        except ModuleNotFoundError:
            result = SandboxResult(
                duration_seconds=time.monotonic() - started,
                error="Modal SDK is not installed.",
            )
        except Exception as exc:
            timed_out = type(exc).__name__ in {
                "ExecTimeoutError",
                "SandboxTimeoutError",
                "TimeoutError",
            }
            result = SandboxResult(
                duration_seconds=time.monotonic() - started,
                timed_out=timed_out,
                error=(
                    "Modal sandbox timed out."
                    if timed_out
                    else f"Modal sandbox failed: {type(exc).__name__}."
                ),
            )
        cleanup_error = _cleanup_modal_sandbox(sandbox)
        if cleanup_error:
            error = f"{result.error} {cleanup_error}" if result.error else cleanup_error
            return result.model_copy(update={"error": error})
        return result


def _stream_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def _cleanup_modal_sandbox(sandbox: Any | None) -> str | None:
    if sandbox is None:
        return None
    failures = []
    try:
        sandbox.terminate(wait=True)
    except Exception as exc:
        failures.append(f"terminate {type(exc).__name__}")
    try:
        sandbox.detach()
    except Exception as exc:
        failures.append(f"detach {type(exc).__name__}")
    if failures:
        return f"Modal sandbox cleanup failed: {', '.join(failures)}."
    return None


def build_sandbox_runner(
    backend: str,
    docker_image: str = DEFAULT_DOCKER_IMAGE,
    modal_app: str = DEFAULT_MODAL_APP,
) -> SandboxRunner:
    if backend == "docker":
        return DockerSandboxRunner(docker_image)
    if backend == "modal":
        return ModalSandboxRunner(modal_app)
    raise ValueError(f"Unsupported sandbox backend: {backend}")
