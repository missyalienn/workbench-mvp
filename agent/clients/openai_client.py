"""OpenAI client factory backed by keyring or environment credentials.

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
from config.settings import settings


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


def get_openai_client() -> OpenAI:
    """Return an authenticated OpenAI client using keyring or env credentials."""
    if settings.OPENAI_USE_KEYCHAIN:
        api_key = keyring.get_password(
            settings.OPENAI_KEYCHAIN_SERVICE,
            settings.OPENAI_KEYCHAIN_LABEL,
        )
        if not api_key:
            logger.error(
                "openai_client.missing_credentials",
                fix=(
                    "Run: keyring set "
                    f"{settings.OPENAI_KEYCHAIN_SERVICE} "
                    f"{settings.OPENAI_KEYCHAIN_LABEL} <your-api-key>"
                ),
            )
            raise AuthError(
                "Missing OpenAI API key in keychain "
                f"(service='{settings.OPENAI_KEYCHAIN_SERVICE}', "
                f"label='{settings.OPENAI_KEYCHAIN_LABEL}'). "
                "Fix: keyring set "
                f"{settings.OPENAI_KEYCHAIN_SERVICE} "
                f"{settings.OPENAI_KEYCHAIN_LABEL} <your-api-key>"
            )
    else:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.error("openai_client.missing_env_credentials", var="OPENAI_API_KEY")
            raise AuthError("Missing required environment variable: OPENAI_API_KEY")

    logger.info("openai_client.initialized")
    return OpenAI(api_key=api_key)


if __name__ == "__main__":
    try:
        get_openai_client()
    except Exception:  # pragma: no cover - manual smoke check
        logger.exception("Failed to initialize OpenAI client.")
