"""Generic retry builder for external service clients.

Each client defines its own `is_retryable` predicate and calls `build_retry`;
this module knows nothing about any specific provider.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from tenacity import after_log, retry, retry_if_exception, stop_after_attempt, wait_random_exponential

from app.config.settings import settings

# stdlib logger: tenacity's after_log requires the logging.Logger interface.
_logger = logging.getLogger(__name__)


def build_retry(*, is_retryable: Callable[[BaseException], bool]) -> Callable:
    """Return a tenacity decorator retrying only exceptions the predicate accepts.

    Attempts/wait come from settings; non-retryable exceptions re-raise immediately.
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
