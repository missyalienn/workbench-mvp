"""Integration tests for api.app exception handlers and routes."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.errors import (
    EXTERNAL_SERVICE_FAILURE,
    INTERNAL_SERVER_ERROR,
    VALIDATION_ERROR,
)
from common.exceptions import (
    AuthError,
    ExternalTimeoutError,
    InvalidResponseError,
    RateLimitError,
)

_PIPELINE = "api.app.run_evidence_pipeline"

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


def test_successful_request_returns_pipeline_result() -> None:
    mock_result = {"search_plan": {}, "evidence_result": "ok"}
    with patch(_PIPELINE, return_value=mock_result):
        response = client.post("/api/run", json={"query": "how to fix a squeaky floor"})

    assert response.status_code == 200
    assert response.json() == mock_result
