"""Generic retry builder for external service clients.

Each client module defines its own `is_retryable` predicate and calls
`build_retry` to get a configured tenacity decorator. This module has no
knowledge of any specific provider (Reddit, OpenAI, etc.).

Usage:
    from services.http.retry_policy import build_retry

    def _is_retryable(exc: Exception) -> bool:
        return isinstance(exc, SomeTransientError)

    _my_retry = build_retry(is_retryable=_is_retryable)

    @_my_retry
    def call_external_service(...):
        ...
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from tenacity import after_log, retry, retry_if_exception, stop_after_attempt, wait_random_exponential

from config.settings import settings

# stdlib logger for tenacity's after_log (requires logging.Logger interface).
_logger = logging.getLogger(__name__)


def build_retry(*, is_retryable: Callable[[Exception], bool]) -> Callable:
    """Return a tenacity retry decorator driven by the provided predicate.

    Retry settings (max attempts, wait) are read from config/settings.py.
    The caller supplies the predicate that determines which exceptions warrant a retry.
    Non-retryable exceptions are re-raised immediately without consuming retry budget.
    """
    return retry(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_random_exponential(
            multiplier=settings.RETRY_WAIT_MULTIPLIER,
            max=settings.RETRY_WAIT_MAX,
        ),
        after=after_log(_logger, logging.WARNING),
        reraise=True,
    )
