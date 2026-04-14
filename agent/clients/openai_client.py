"""OpenAI client factory backed by keyring credentials.

Example:
    client = get_openai_client()
    response = client.responses.create(model="gpt-4.1-mini", input="Hello!")
"""

from __future__ import annotations

import keyring
import openai
from openai import OpenAI

from common.exceptions import AuthError, ExternalServiceError, ExternalTimeoutError, InvalidResponseError, RateLimitError
from config.logging_config import get_logger


logger = get_logger(__name__)


def translate_openai_error(exc: Exception) -> ExternalServiceError:
    """Translate an OpenAI SDK exception to a typed ExternalServiceError.

    Use this at any OpenAI API call site so that raw SDK exceptions never
    cross service boundaries. Non-OpenAI exceptions (e.g. JSONDecodeError,
    ValidationError from response parsing) fall through to InvalidResponseError.
    """
    if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
        return AuthError(str(exc))
    if isinstance(exc, openai.RateLimitError):
        return RateLimitError(str(exc))
    if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)):
        return ExternalTimeoutError(str(exc))
    if isinstance(exc, openai.APIError):
        return InvalidResponseError(str(exc))
    return InvalidResponseError(str(exc))


def get_openai_client(environment: str = "openai-dev") -> OpenAI:
    """Return an authenticated OpenAI client using keyring credentials."""
    api_key = keyring.get_password("openai-key", environment)
    if not api_key:
        logger.error(
            "openai_client.missing_credentials",
            environment=environment,
            fix="Run: keyring set openai-key <environment> <your-api-key>",
        )
        raise RuntimeError(
            f"Missing OpenAI API key in keyring (environment='{environment}'). "
            f"Fix: keyring set openai-key {environment} <your-api-key>"
        )

    logger.info("openai_client.initialized", environment=environment)
    return OpenAI(api_key=api_key)


if __name__ == "__main__":
    try:
        get_openai_client()
    except Exception:  # pragma: no cover - manual smoke check
        logger.exception("Failed to initialize OpenAI client.")
