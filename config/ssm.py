"""Resolve production secrets from AWS SSM Parameter Store.

Usage:
    token = resolve_env_or_ssm_secret(
        current_value=settings.PROXY_TOKEN,
        ssm_parameter_name=settings.PROXY_TOKEN_SSM_PARAMETER,
        secret_name="PROXY_TOKEN",
    )
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from common.exceptions import AuthError
from config.logging_config import get_logger

logger = get_logger(__name__)


def _build_ssm_client() -> Any:
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - depends on runtime packaging
        raise AuthError("boto3 is required to load production secrets from AWS SSM.") from exc

    return boto3.client("ssm")


@lru_cache(maxsize=32)
def load_secure_parameter(parameter_name: str) -> str:
    """Fetch a decrypted SecureString parameter value from AWS SSM."""
    try:
        response = _build_ssm_client().get_parameter(
            Name=parameter_name,
            WithDecryption=True,
        )
    except Exception as exc:
        raise AuthError(
            f"Failed to load required SSM parameter: {parameter_name}"
        ) from exc

    value = response.get("Parameter", {}).get("Value")
    if not value:
        raise AuthError(f"SSM parameter was empty: {parameter_name}")

    logger.info("ssm.parameter_loaded", parameter_name=parameter_name)
    return value


def resolve_env_or_ssm_secret(
    *,
    current_value: str | None,
    ssm_parameter_name: str | None,
    secret_name: str,
) -> str | None:
    """Prefer an already configured value, else fall back to AWS SSM."""
    if current_value:
        return current_value

    if not ssm_parameter_name:
        return None

    logger.info("ssm.secret_resolve", secret_name=secret_name)
    return load_secure_parameter(ssm_parameter_name)
