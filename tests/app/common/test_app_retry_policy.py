import pytest

from app.common import retry_policy
from app.common.exceptions import AuthError, ExternalServiceError, RateLimitError
from app.config.settings import settings


@pytest.fixture(autouse=True)
def _fast_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RETRY_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(settings, "RETRY_WAIT_MAX", 0)


def test_retries_retryable_then_succeeds() -> None:
    calls = {"n": 0}

    @retry_policy.build_retry(is_retryable=lambda e: isinstance(e, RateLimitError))
    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RateLimitError("429")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_non_retryable_raises_immediately() -> None:
    calls = {"n": 0}

    @retry_policy.build_retry(is_retryable=lambda e: isinstance(e, RateLimitError))
    def bad() -> None:
        calls["n"] += 1
        raise AuthError("nope")

    with pytest.raises(AuthError):
        bad()
    assert calls["n"] == 1


def test_exhausted_attempts_reraises_original() -> None:
    @retry_policy.build_retry(is_retryable=lambda e: True)
    def always() -> None:
        raise RateLimitError("429")

    with pytest.raises(RateLimitError):
        always()


def test_taxonomy_subclasses_external_service_error() -> None:
    assert issubclass(AuthError, ExternalServiceError)
    assert issubclass(RateLimitError, ExternalServiceError)
