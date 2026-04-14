"""Internal exception taxonomy for Workbench.

Exceptions are named by failure category, not by the service that raised them.
All ExternalServiceError subclasses map to HTTP 502 at the API boundary.
"""

from __future__ import annotations


class ExternalServiceError(Exception):
    """Base class for all external service failures.

    Raised when a dependency (OpenAI, Reddit, etc.) fails to fulfill a request.
    Maps to HTTP 502 at the API boundary.
    """


class AuthError(ExternalServiceError):
    """Authentication or authorization failure with an external service."""


class RateLimitError(ExternalServiceError):
    """Rate limit exhausted after retries. The upstream returned 429 and retries failed."""


class ExternalTimeoutError(ExternalServiceError):
    """Request to an external service timed out after retries."""


class InvalidResponseError(ExternalServiceError):
    """An external service returned an invalid, unparseable, or contract-violating response."""
