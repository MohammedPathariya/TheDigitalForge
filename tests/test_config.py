import pytest

from backend.config import Settings


def test_api_key_is_required_only_when_a_run_starts() -> None:
    settings = Settings(openai_api_key=None)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        settings.require_openai_api_key()


def test_attempt_limit_cannot_exceed_architecture_limit() -> None:
    with pytest.raises(ValueError):
        Settings(max_attempts=4)
