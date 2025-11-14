"""Shared retry helpers for HTTP-based clients (e.g., Reddit API)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from config.settings import settings

from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


class RateLimitError(RuntimeError):
    """429 Rate Limit Error"""


class RetryableFetchError(RuntimeError):
    """Raised for retryable transport/server failures (timeouts, 5xx, etc.)."""


def fetch_with_retry(logger: logging.Logger | None = None) -> Callable:
    """Return a Tenacity decorator configured for our default retry policy."""
    log = logger or logging.getLogger(__name__)
    return retry(
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_random_exponential(multiplier=settings.RETRY_WAIT_MULTIPLIER, max=settings.RETRY_WAIT_MAX),
        retry=retry_if_exception_type((RateLimitError, RetryableFetchError)),
        after=after_log(log, logging.INFO),
        reraise=True,
    )   
