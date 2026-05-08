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
