"""OpenAI-backed LLM client for the curator.
This module is the hard boundary between:
- internal prompt messages (PromptMessage) and the external validated, structured DTO output (CurationResult).
It must never return raw text to callers.
"""

from __future__ import annotations

from openai import OpenAI
from pydantic import ValidationError

from services.summarizer.models import CurationResult

from .errors import LLMStructuredOutputError, LLMTransportError
from .types import LLMClient, PromptMessage


class OpenAILLMClient(LLMClient):
    """Production LLM client implementation using OpenAI Responses API with structured outputs."""

    def __init__(self, *, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def summarize_structured(self, *, messages: list[PromptMessage]) -> CurationResult:
        """Return a validated CurationResult or raise a typed error."""
        payload = [ {"role": message.role, "content": message.content} for message in messages]
      

        try:
            response = self._client.responses.parse(
                model=self._model,
                input=payload,
                text_format=CurationResult,
            )

        except ValidationError as e:
            raise LLMStructuredOutputError(
                "OpenAI response failed schema validation",
                details={"model": self._model, "exc_type": type(e).__name__},
                cause=e,
            ) from e

        except Exception as e:
            # Network/auth/rate-limit/service errors typically land here.
            raise LLMTransportError(
                "Failed to call OpenAI Responses API",
                details={"model": self._model, "exc_type": type(e).__name__},
                cause=e,
            ) from e

        parsed = response.output_parsed
        if parsed is None:
            raise LLMStructuredOutputError(
                "OpenAI response did not return a parsed CurationResult",
                details={"model": self._model},
            )

        return parsed
