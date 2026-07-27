import pytest

from backend.config import Settings


def test_api_key_is_required_only_when_a_run_starts() -> None:
    settings = Settings(openai_api_key=None)

    assert settings.openai_model_name == "gpt-4o-mini"
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        settings.require_openai_api_key()


def test_attempt_limit_cannot_exceed_architecture_limit() -> None:
    with pytest.raises(ValueError):
        Settings(max_attempts=4)


def test_sandbox_limits_are_typed_and_bounded() -> None:
    settings = Settings(sandbox_backend="modal", sandbox_memory_mib=512)

    assert settings.sandbox_backend == "modal"
    assert settings.sandbox_memory_mib == 512
    with pytest.raises(ValueError):
        Settings(sandbox_process_limit=2)


def test_public_demo_controls_are_typed_and_bounded() -> None:
    settings = Settings(
        max_daily_model_runs=5,
        rate_limit_requests=3,
        rate_limit_window_seconds=30,
        run_timeout_seconds=120,
    )

    assert settings.max_active_runs == 1
    assert settings.max_daily_model_runs == 5
    with pytest.raises(ValueError):
        Settings(max_active_runs=2)
    with pytest.raises(ValueError):
        Settings(run_timeout_seconds=0)
