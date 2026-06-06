"""Integration tests for api.app exception handlers and routes."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.app import LIVE_RUNS_DISABLED_MESSAGE, PROXY_TOKEN_HEADER, app
from api.errors import (
    EXTERNAL_SERVICE_FAILURE,
    INTERNAL_SERVER_ERROR,
    VALIDATION_ERROR,
)
from api.models import ClientThread, EvidenceResponse, SearchPlan
from common.exceptions import (
    AuthError,
    ExternalTimeoutError,
    InvalidResponseError,
    RateLimitError,
)

_PIPELINE = "api.app.run_pipeline"

client = TestClient(app, raise_server_exceptions=False)


# --- Exception handler mapping ---


@pytest.mark.parametrize("exc,expected_status,expected_type", [
    (AuthError("auth failed"),                  502, EXTERNAL_SERVICE_FAILURE),
    (RateLimitError("rate limited"),            502, EXTERNAL_SERVICE_FAILURE),
    (ExternalTimeoutError("timed out"),         502, EXTERNAL_SERVICE_FAILURE),
    (InvalidResponseError("bad response"),      502, EXTERNAL_SERVICE_FAILURE),
    (RuntimeError("unexpected"),                500, INTERNAL_SERVER_ERROR),
])
def test_exception_maps_to_correct_status_and_type(
    exc: Exception, expected_status: int, expected_type: str
) -> None:
    with patch(_PIPELINE, side_effect=exc):
        response = client.post("/api/run", json={"query": "valid query"})

    assert response.status_code == expected_status
    body = response.json()
    assert body["type"] == expected_type
    assert body["status"] == expected_status


# --- Content-Type ---


@pytest.mark.parametrize("exc", [
    AuthError("x"),
    RateLimitError("x"),
    ExternalTimeoutError("x"),
    InvalidResponseError("x"),
    RuntimeError("x"),
])
def test_error_response_content_type(exc: Exception) -> None:
    with patch(_PIPELINE, side_effect=exc):
        response = client.post("/api/run", json={"query": "valid query"})

    assert "application/problem+json" in response.headers["content-type"]


# --- Detail strings are generic, not internal exception messages ---


@pytest.mark.parametrize("exc", [
    AuthError("sensitive internal detail"),
    RuntimeError("sensitive internal detail"),
])
def test_error_detail_does_not_leak_internal_message(exc: Exception) -> None:
    with patch(_PIPELINE, side_effect=exc):
        response = client.post("/api/run", json={"query": "valid query"})

    assert "sensitive internal detail" not in response.json()["detail"]


# --- Request validation ---


def test_blank_query_returns_422() -> None:
    response = client.post("/api/run", json={"query": "   "})
    assert response.status_code == 422
    body = response.json()
    assert body["type"] == VALIDATION_ERROR
    assert "application/problem+json" in response.headers["content-type"]


def test_missing_query_field_returns_422() -> None:
    response = client.post("/api/run", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["type"] == VALIDATION_ERROR
    assert "application/problem+json" in response.headers["content-type"]


# --- Happy path ---


def test_healthcheck_returns_ok() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_rejects_missing_proxy_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.app.settings.PROXY_TOKEN", "expected-token")

    response = client.post("/api/run", json={"query": "valid query"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_run_rejects_incorrect_proxy_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.app.settings.PROXY_TOKEN", "expected-token")

    response = client.post(
        "/api/run",
        json={"query": "valid query"},
        headers={PROXY_TOKEN_HEADER: "wrong-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_run_accepts_ssm_loaded_proxy_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.app.settings.LIVE_RUNS_ENABLED", True)
    monkeypatch.setattr("api.app.settings.PROXY_TOKEN", None)
    monkeypatch.setattr("api.app.settings.PROXY_TOKEN_SSM_PARAMETER", "/workbench/prod/proxy_token")
    monkeypatch.setattr(
        "api.app.resolve_env_or_ssm_secret",
        lambda **kwargs: "expected-token",
    )

    mock_result = EvidenceResponse(
        search_plan=SearchPlan(search_terms=["squeaky floor fix"], subreddits=["DIY"]),
        status="ok",
        summary="Most threads recommend injecting construction adhesive between the subfloor and joist.",
        threads=[
            ClientThread(
                rank=1,
                title="Fix squeaky floor without removing carpet",
                subreddit="DIY",
                url="https://www.reddit.com/r/DIY/comments/abc123/",
                relevance_score=0.91,
                post_karma=250,
                num_comments=18,
            )
        ],
        limitations=[],
    )
    with patch(_PIPELINE, return_value=mock_result):
        response = client.post(
            "/api/run",
            json={"query": "how to fix a squeaky floor"},
            headers={PROXY_TOKEN_HEADER: "expected-token"},
        )

    assert response.status_code == 200


def test_run_returns_503_when_live_runs_are_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.app.settings.LIVE_RUNS_ENABLED", False)

    response = client.post("/api/run", json={"query": "valid query"})

    assert response.status_code == 503
    assert response.json() == {"detail": LIVE_RUNS_DISABLED_MESSAGE}


def test_successful_request_returns_pipeline_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.app.settings.LIVE_RUNS_ENABLED", True)
    monkeypatch.setattr("api.app.settings.PROXY_TOKEN", None)
    mock_result = EvidenceResponse(
        search_plan=SearchPlan(search_terms=["squeaky floor fix"], subreddits=["DIY"]),
        status="ok",
        summary="Most threads recommend injecting construction adhesive between the subfloor and joist.",
        threads=[
            ClientThread(
                rank=1,
                title="Fix squeaky floor without removing carpet",
                subreddit="DIY",
                url="https://www.reddit.com/r/DIY/comments/abc123/",
                relevance_score=0.91,
                post_karma=250,
                num_comments=18,
            )
        ],
        limitations=[],
    )
    with patch(_PIPELINE, return_value=mock_result):
        response = client.post(
            "/api/run",
            json={"query": "how to fix a squeaky floor"},
            headers={PROXY_TOKEN_HEADER: "expected-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["summary"] == mock_result.summary
    assert len(body["threads"]) == 1
    assert body["threads"][0]["title"] == mock_result.threads[0].title
