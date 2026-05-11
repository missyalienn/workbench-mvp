"""Unit tests for Reddit client authentication configuration."""

from __future__ import annotations

import pytest

from common.exceptions import AuthError
from config.settings import settings
from services.reddit_client.client import RedditClient
from services.reddit_client.session import AsyncRedditSession


def test_reddit_client_uses_keyring_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Client should build a keyring-backed session when configured to do so."""
    sentinel = object()
    monkeypatch.setattr(settings, "REDDIT_USE_KEYCHAIN", True)
    monkeypatch.setattr(
        "services.reddit_client.client.AsyncRedditSession.from_keyring",
        lambda: sentinel,
    )
    monkeypatch.setattr(
        "services.reddit_client.client.AsyncRedditSession.from_env",
        lambda: object(),
    )

    client = RedditClient()

    assert client._session_manager is sentinel


def test_reddit_client_uses_env_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Client should build an env-backed session when keyring auth is disabled."""
    sentinel = object()
    monkeypatch.setattr(settings, "REDDIT_USE_KEYCHAIN", False)
    monkeypatch.setattr(
        "services.reddit_client.client.AsyncRedditSession.from_env",
        lambda: sentinel,
    )
    monkeypatch.setattr(
        "services.reddit_client.client.AsyncRedditSession.from_keyring",
        lambda: object(),
    )

    client = RedditClient()

    assert client._session_manager is sentinel


def test_reddit_session_from_env_raises_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env mode should raise when required Reddit credentials are unset."""
    monkeypatch.setattr(settings, "REDDIT_CLIENT_ID", None)
    monkeypatch.setattr(settings, "REDDIT_CLIENT_SECRET", None)

    with pytest.raises(AuthError) as excinfo:
        AsyncRedditSession.from_env()

    assert "Missing required environment variables" in str(excinfo.value)
    assert "REDDIT_CLIENT_ID" in str(excinfo.value)
    assert "REDDIT_CLIENT_SECRET" in str(excinfo.value)


def test_reddit_session_from_keyring_raises_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keyring mode should raise when stored Reddit credentials are unavailable."""
    monkeypatch.setattr(
        "services.reddit_client.session.keyring.get_password",
        lambda service, label: None,
    )

    with pytest.raises(AuthError) as excinfo:
        AsyncRedditSession.from_keyring()

    assert "Missing Reddit API credentials in keychain" in str(excinfo.value)
    assert settings.REDDIT_KEYCHAIN_LABEL in str(excinfo.value)


def test_reddit_session_from_env_uses_ssm_when_env_credentials_are_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "REDDIT_CLIENT_ID", None)
    monkeypatch.setattr(settings, "REDDIT_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "REDDIT_CLIENT_ID_SSM_PARAMETER", "/workbench/prod/reddit_client_id")
    monkeypatch.setattr(settings, "REDDIT_CLIENT_SECRET_SSM_PARAMETER", "/workbench/prod/reddit_client_secret")
    monkeypatch.setattr(settings, "REDDIT_USER_AGENT", "Workbench/1.0 by /u/chippetto90")
    monkeypatch.setattr(settings, "REDDIT_USER_AGENT_SSM_PARAMETER", "/workbench/prod/reddit_user_agent")

    def _resolve_secret(**kwargs: str | None) -> str | None:
        secret_name = kwargs["secret_name"]
        if secret_name == "REDDIT_CLIENT_ID":
            return "ssm-client-id"
        if secret_name == "REDDIT_CLIENT_SECRET":
            return "ssm-client-secret"
        if secret_name == "REDDIT_USER_AGENT":
            return "ssm-user-agent"
        return None

    monkeypatch.setattr(
        "services.reddit_client.session.resolve_env_or_ssm_secret",
        _resolve_secret,
    )

    session = AsyncRedditSession.from_env()

    assert session.client_id == "ssm-client-id"
    assert session.client_secret == "ssm-client-secret"
    assert session.user_agent == "ssm-user-agent"
