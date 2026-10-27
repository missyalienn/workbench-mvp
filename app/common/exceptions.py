"""Internal exception taxonomy for the V2 ingest/agent stack.

Exceptions are named by failure category, not by the service that raised them.
"""

from __future__ import annotations


class ExternalServiceError(Exception):
    """Base class for all external service failures (Reddit, OpenAI, Pinecone, etc.)."""


class AuthError(ExternalServiceError):
    """Authentication or authorization failure with an external service."""


class RateLimitError(ExternalServiceError):
    """Rate limit exhausted after retries. The upstream returned 429 and retries failed."""


class ExternalTimeoutError(ExternalServiceError):
    """Request to an external service timed out after retries."""


class InvalidResponseError(ExternalServiceError):
    """An external service returned an invalid, unparseable, or contract-violating response."""
