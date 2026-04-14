"""OpenAI-backed LLM client for the curator.
This module is the hard boundary between:
- internal prompt messages (PromptMessage) and the external validated, structured DTO output (CurationResult).
It must never return raw text to callers.
"""

from __future__ import annotations

import time

from openai import OpenAI

from agent.clients.openai_client import translate_openai_error
from config.logging_config import get_logger
from common.exceptions import InvalidResponseError
from services.synthesizer.models import EvidenceResult

from .types import LLMClient, PromptMessage

logger = get_logger(__name__)


class OpenAILLMClient(LLMClient):
    """Production LLM client implementation using OpenAI Responses API with structured outputs."""

    def __init__(self, *, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def summarize_structured(self, *, messages: list[PromptMessage]) -> EvidenceResult:
        """Return a validated CurationResult or raise a typed error."""
        t0 = time.monotonic()
        logger.info("synthesizer.start", model=self._model, n_messages=len(messages))
        payload = [{"role": message.role, "content": message.content} for message in messages]

        try:
            response = self._client.responses.parse(
                model=self._model,
                input=payload,
                text_format=EvidenceResult,
            )

        except Exception as e:
            logger.error("synthesizer.failed", elapsed_ms=int((time.monotonic() - t0) * 1000), error=str(e), exc_type=type(e).__name__)
            raise translate_openai_error(e) from e

        parsed = response.output_parsed
        if parsed is None:
            logger.error("synthesizer.failed", elapsed_ms=int((time.monotonic() - t0) * 1000), error="output_parsed is None")
            raise InvalidResponseError("OpenAI returned no parsed output")

        logger.info("synthesizer.complete", elapsed_ms=int((time.monotonic() - t0) * 1000), status=parsed.status, n_threads=len(parsed.threads) if parsed.threads else 0)
        return parsed
