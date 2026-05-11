"""Unit tests for AWS SSM secret loading helpers."""

from __future__ import annotations

import pytest

from common.exceptions import AuthError
from config.ssm import load_secure_parameter, resolve_env_or_ssm_secret


class _SSMClientStub:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def get_parameter(self, *, Name: str, WithDecryption: bool) -> dict[str, dict[str, str | None]]:
        return {"Parameter": {"Value": self._value}}


def test_resolve_env_or_ssm_secret_prefers_current_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("config.ssm.load_secure_parameter", lambda name: "ssm-value")

    resolved = resolve_env_or_ssm_secret(
        current_value="env-value",
        ssm_parameter_name="/workbench/prod/openai_api_key",
        secret_name="OPENAI_API_KEY",
    )

    assert resolved == "env-value"


def test_load_secure_parameter_returns_ssm_value(monkeypatch: pytest.MonkeyPatch) -> None:
    load_secure_parameter.cache_clear()
    monkeypatch.setattr("config.ssm._build_ssm_client", lambda: _SSMClientStub("secret-value"))

    resolved = load_secure_parameter("/workbench/prod/proxy_token")

    assert resolved == "secret-value"


def test_load_secure_parameter_raises_for_empty_value(monkeypatch: pytest.MonkeyPatch) -> None:
    load_secure_parameter.cache_clear()
    monkeypatch.setattr("config.ssm._build_ssm_client", lambda: _SSMClientStub(None))

    with pytest.raises(AuthError) as excinfo:
        load_secure_parameter("/workbench/prod/proxy_token")

    assert "SSM parameter was empty" in str(excinfo.value)
