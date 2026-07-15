"""Failure classification and safe repair evidence for generated code."""

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .sandbox import SandboxResult

MAX_REPAIR_OUTPUT_CHARACTERS = 8_000
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CREDENTIAL = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
_OPENAI_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
_TEMP_SANDBOX_PATH = re.compile(r"/[^\s:'\"]*digital-forge-sandbox-[^/\s:'\"]+")
_RESOURCE_MARKERS = (
    "cannot allocate memory",
    "memoryerror",
    "out of memory",
    "resource temporarily unavailable",
    "too many open files",
)


class FailureKind(str, Enum):
    candidate = "candidate"
    test = "test"
    timeout = "timeout"
    resource = "resource"
    infrastructure = "infrastructure"


class RepairTarget(str, Enum):
    developer = "developer"
    tester = "tester"
    system = "system"


class RepairEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    failure_kind: FailureKind
    target: RepairTarget
    summary: str
    stdout: str = ""
    stderr: str = ""

    @property
    def consumes_attempt(self) -> bool:
        return self.failure_kind is not FailureKind.infrastructure

    def as_prompt(self) -> str:
        return (
            "TESTS FAILED:\n"
            f"FAILURE CLASS: {self.failure_kind.value}\n"
            f"RESPONSIBLE AGENT: {self.target.value}\n"
            f"REPAIR GUIDANCE: {self.summary}\n"
            f"--- STDOUT ---\n{self.stdout or '<empty>'}\n"
            f"--- STDERR ---\n{self.stderr or '<empty>'}"
        )


def build_repair_evidence(
    result: SandboxResult,
    *,
    code_file_path: str,
    test_file_path: str,
) -> RepairEvidence:
    """Classify a failed sandbox result and expose bounded, sanitized evidence."""
    stdout = sanitize_output(result.stdout)
    stderr = sanitize_output(result.stderr)
    combined = f"{stdout}\n{stderr}".lower()

    if result.timed_out or result.exit_code == 124:
        return RepairEvidence(
            failure_kind=FailureKind.timeout,
            target=RepairTarget.developer,
            summary="Candidate execution exceeded the wall-time limit. Remove blocking or unbounded work.",
            stdout=stdout,
            stderr=stderr,
        )
    if result.exit_code in {-9, 137} or any(
        marker in combined for marker in _RESOURCE_MARKERS
    ):
        return RepairEvidence(
            failure_kind=FailureKind.resource,
            target=RepairTarget.developer,
            summary="Candidate execution exceeded a sandbox resource limit. Reduce its resource use.",
            stdout=stdout,
            stderr=stderr,
        )
    if result.error:
        return RepairEvidence(
            failure_kind=FailureKind.infrastructure,
            target=RepairTarget.system,
            summary=sanitize_output(result.error),
            stdout=stdout,
            stderr=stderr,
        )
    if _is_test_failure(combined, code_file_path, test_file_path, result.exit_code):
        return RepairEvidence(
            failure_kind=FailureKind.test,
            target=RepairTarget.tester,
            summary="The test suite failed before it could validly evaluate the candidate. Repair only the tests.",
            stdout=stdout,
            stderr=stderr,
        )
    return RepairEvidence(
        failure_kind=FailureKind.candidate,
        target=RepairTarget.developer,
        summary="The candidate failed the generated test suite. Diagnose the assertion or exception and repair only the application code.",
        stdout=stdout,
        stderr=stderr,
    )


def failure_kind_from_output(output: str) -> FailureKind | None:
    match = re.search(r"^FAILURE CLASS:\s*([a-z]+)\s*$", output, re.MULTILINE)
    if match is None:
        return None
    try:
        return FailureKind(match.group(1))
    except ValueError:
        return None


def sanitize_output(value: str) -> str:
    """Remove terminal controls, credentials, host paths, and excessive output."""
    cleaned = _ANSI_ESCAPE.sub("", value.replace("/workspace", "<workspace>"))
    cleaned = _TEMP_SANDBOX_PATH.sub("<sandbox>", cleaned)
    cleaned = _CREDENTIAL.sub(r"\1\2<redacted>", cleaned)
    cleaned = _OPENAI_KEY.sub("<redacted>", cleaned)
    cleaned = _CONTROL_CHARACTERS.sub("", cleaned)
    if len(cleaned) <= MAX_REPAIR_OUTPUT_CHARACTERS:
        return cleaned
    marker = "\n... <output truncated>"
    return cleaned[: MAX_REPAIR_OUTPUT_CHARACTERS - len(marker)] + marker


def _is_test_failure(
    output: str,
    code_file_path: str,
    test_file_path: str,
    exit_code: int | None,
) -> bool:
    if exit_code == 5 or "no tests ran" in output:
        return True
    test_name = rf"(?<![A-Za-z0-9_]){re.escape(test_file_path.lower())}"
    code_name = rf"(?<![A-Za-z0-9_]){re.escape(code_file_path.lower())}"
    test_error = re.search(
        rf"(?:syntaxerror|indentationerror).*{test_name}|{test_name}.*(?:syntaxerror|indentationerror)",
        output,
        re.DOTALL,
    )
    code_error = re.search(
        rf"(?:syntaxerror|indentationerror).*{code_name}|{code_name}.*(?:syntaxerror|indentationerror)",
        output,
        re.DOTALL,
    )
    return test_error is not None and code_error is None
