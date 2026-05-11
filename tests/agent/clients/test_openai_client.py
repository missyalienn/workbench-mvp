"""Unit tests for OpenAI client authentication configuration."""

from __future__ import annotations

import pytest

from agent.clients.openai_client import get_openai_client
from common.exceptions import AuthError
from config.settings import settings


def test_get_openai_client_raises_without_keyring_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keyring mode should raise when the stored API key is unavailable."""
    monkeypatch.setattr(settings, "OPENAI_USE_KEYCHAIN", True)
    monkeypatch.setattr(
        "agent.clients.openai_client.keyring.get_password",
        lambda service, label: None,
    )

    with pytest.raises(AuthError) as excinfo:
        get_openai_client()

    assert "Missing OpenAI API key in keychain" in str(excinfo.value)
    assert settings.OPENAI_KEYCHAIN_LABEL in str(excinfo.value)


def test_get_openai_client_raises_without_env_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env mode should raise when OPENAI_API_KEY is unset."""
    monkeypatch.setattr(settings, "OPENAI_USE_KEYCHAIN", False)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    with pytest.raises(AuthError) as excinfo:
        get_openai_client()

    assert "Missing required environment variable: OPENAI_API_KEY" in str(excinfo.value)


def test_get_openai_client_uses_ssm_when_env_credentials_are_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "OPENAI_USE_KEYCHAIN", False)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_API_KEY_SSM_PARAMETER", "/workbench/prod/openai_api_key")
    monkeypatch.setattr(
        "agent.clients.openai_client.resolve_env_or_ssm_secret",
        lambda **kwargs: "ssm-openai-key",
    )
    monkeypatch.setattr(
        "agent.clients.openai_client.OpenAI",
        lambda api_key: {"api_key": api_key},
    )

    client = get_openai_client()

    assert client == {"api_key": "ssm-openai-key"}
