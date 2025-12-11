"""Unit tests for agent.clients.openai_client."""

from __future__ import annotations

import pytest

from agent.clients.openai_client import get_openai_client


def test_get_openai_client_raises_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Factory should raise when API credentials are unavailable."""
    monkeypatch.setattr(
        "agent.clients.openai_client.keyring.get_password",
        lambda service, environment: None,
    )

    with pytest.raises(RuntimeError) as excinfo:
        get_openai_client(environment="test-env")

    assert "Missing OpenAI credentials" in str(excinfo.value)
