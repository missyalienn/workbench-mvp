"""Exception types for the curator LLM execution layer."""

from __future__ import annotations

from typing import Any


class SummarizerLLMError(Exception):
    """Base class for all curator LLM execution layer errors.

    Attributes:
        details: Optional structured context for logging/diagnostics.
        cause: Optional underlying exception that triggered this error.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.details = details
        self.cause = cause


class LLMTransportError(SummarizerLLMError):
    """Network/provider failures (timeouts, auth, rate limits, service errors)."""


class LLMStructuredOutputError(SummarizerLLMError):
    """Failed to obtain a valid structured CurationResult (schema/validation/parsing)."""


class ContractViolationError(SummarizerLLMError):
    """A valid DTO was returned, but it violated curator contract rules (budgets/caps/version)."""
