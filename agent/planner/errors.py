"""Exception types for the planner agent."""

from __future__ import annotations

from typing import Any


class PlannerError(Exception):
    """LLM or upstream failure while generating a search plan.

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
