from backend.sandbox import SandboxResult
from backend.self_healing import (
    MAX_REPAIR_OUTPUT_CHARACTERS,
    FailureKind,
    RepairEvidence,
    RepairTarget,
    build_repair_evidence,
    failure_kind_from_output,
    infrastructure_retryable_from_output,
    sanitize_output,
)


def _evidence(result: SandboxResult) -> RepairEvidence:
    return build_repair_evidence(
        result,
        code_file_path="solution.py",
        test_file_path="test_solution.py",
    )


def test_classifies_timeout_resource_and_infrastructure_failures() -> None:
    timeout = _evidence(
        SandboxResult(duration_seconds=10, timed_out=True, error="host timeout")
    )
    resource = _evidence(
        SandboxResult(duration_seconds=1, exit_code=137, stderr="Killed")
    )
    infrastructure = _evidence(
        SandboxResult(duration_seconds=0.1, error="Docker is unavailable")
    )

    assert timeout.failure_kind is FailureKind.timeout
    assert timeout.target is RepairTarget.developer
    assert timeout.consumes_attempt is True
    assert resource.failure_kind is FailureKind.resource
    assert resource.target is RepairTarget.developer
    assert infrastructure.failure_kind is FailureKind.infrastructure
    assert infrastructure.target is RepairTarget.system
    assert infrastructure.consumes_attempt is False


def test_classifies_candidate_and_broken_test_failures() -> None:
    candidate = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=1,
            stdout="test_solution.py::test_answer FAILED\nE assert 1 == 2",
        )
    )
    broken_test = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=2,
            stderr='File "/workspace/test_solution.py", line 1\nSyntaxError',
        )
    )

    assert candidate.failure_kind is FailureKind.candidate
    assert candidate.target is RepairTarget.developer
    assert broken_test.failure_kind is FailureKind.test
    assert broken_test.target is RepairTarget.tester
    assert failure_kind_from_output(broken_test.as_prompt()) is FailureKind.test


def test_application_syntax_failure_routes_to_developer_with_contract_guidance() -> (
    None
):
    candidate = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=1,
            stderr='File "/workspace/solution.py", line 3\nSyntaxError: invalid syntax',
        )
    )

    assert candidate.failure_kind is FailureKind.candidate
    assert candidate.target is RepairTarget.developer
    assert "exact function names" in candidate.summary


def test_missing_supported_dependency_is_non_retryable_infrastructure() -> None:
    infrastructure = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=2,
            stdout=(
                "test_solution.py:2: in <module>\n"
                "    from fastapi import FastAPI\n"
                "E   ModuleNotFoundError: No module named 'fastapi'"
            ),
        )
    )

    assert infrastructure.failure_kind is FailureKind.infrastructure
    assert infrastructure.target is RepairTarget.system
    assert infrastructure.retryable is False
    assert infrastructure_retryable_from_output(infrastructure.as_prompt()) is False


def test_missing_pydantic_email_validator_is_sandbox_infrastructure() -> None:
    infrastructure = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=2,
            stdout=(
                "solution.py:2: in <module>\n"
                "E   ModuleNotFoundError: No module named 'email_validator'\n"
                "E   ImportError: email-validator is not installed"
            ),
        )
    )

    assert infrastructure.failure_kind is FailureKind.infrastructure
    assert infrastructure.target is RepairTarget.system
    assert infrastructure.retryable is False


def test_unrequested_missing_dependency_routes_to_the_file_that_imported_it() -> None:
    broken_test = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=2,
            stdout=(
                "test_solution.py:1: in <module>\n"
                "    import hypothesis\n"
                "E   ModuleNotFoundError: No module named 'hypothesis'"
            ),
        )
    )
    candidate = _evidence(
        SandboxResult(
            duration_seconds=0.1,
            exit_code=2,
            stdout=(
                "test_solution.py:1: in <module>\n"
                "    from solution import answer\n"
                "solution.py:1: in <module>\n"
                "    import hypothesis\n"
                "E   ModuleNotFoundError: No module named 'hypothesis'"
            ),
        )
    )

    assert broken_test.failure_kind is FailureKind.test
    assert broken_test.target is RepairTarget.tester
    assert "outside the declared sandbox capability set" in broken_test.summary
    assert candidate.failure_kind is FailureKind.candidate
    assert candidate.target is RepairTarget.developer
    assert "outside the declared sandbox capability set" in candidate.summary


def test_sanitizes_and_bounds_repair_output() -> None:
    raw = (
        "\x1b[31m/workspace/solution.py\x1b[0m "
        "api_key=super-secret sk-1234567890 \x00" + "x" * 10_000
    )

    sanitized = sanitize_output(raw)

    assert "\x1b" not in sanitized
    assert "\x00" not in sanitized
    assert "super-secret" not in sanitized
    assert "sk-1234567890" not in sanitized
    assert "<workspace>/solution.py" in sanitized
    assert sanitized.endswith("... <output truncated>")
    assert len(sanitized) == MAX_REPAIR_OUTPUT_CHARACTERS
