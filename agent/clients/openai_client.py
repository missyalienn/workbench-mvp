"""OpenAI client factory backed by keyring credentials.

Example:
    client = get_openai_client()
    response = client.responses.create(model="gpt-4.1-mini", input="Hello!")
"""

from __future__ import annotations

import keyring
from openai import OpenAI

from config.logging_config import get_logger


logger = get_logger(__name__)


def get_openai_client(environment: str = "openai-dev") -> OpenAI:
    """Return an authenticated OpenAI client using keyring credentials."""
    api_key = keyring.get_password("openai-key", environment)
    if not api_key:
        logger.error("openai_client.missing_credentials", environment=environment)
        raise RuntimeError(f"Missing OpenAI credentials in keyring for environment: {environment}.")

    logger.info("openai_client.initialized", environment=environment)
    return OpenAI(api_key=api_key)


if __name__ == "__main__":
    try:
        get_openai_client()
    except Exception:  # pragma: no cover - manual smoke check
        logger.exception("Failed to initialize OpenAI client.")
