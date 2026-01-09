"""Shared types for the summarizer LLM execution layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from services.summarizer.models import SummarizeResult

MessageRole = Literal["system", "user", "assistant"]

@dataclass(frozen=True)
class PromptMessage:
    role: MessageRole
    content: str


class LLMClient(Protocol):
    """ Structured output interface for an LLM client used by the summarizer. """

    def summarize_structured(
        self,
        *,
        messages: list[PromptMessage],
    ) -> SummarizeResult:
        ...