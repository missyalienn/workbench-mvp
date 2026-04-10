"""Integration tests for api.app exception handlers and routes."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from agent.planner.errors import PlannerError
from api.app import app
from api.errors import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    SYNTHESIS_CONTRACT_FAILURE,
    UPSTREAM_FAILURE,
    VALIDATION_ERROR,
)
from services.reddit_client.session import RedditAuthError
from services.synthesizer.llm_execution.errors import LLMStructuredOutputError, LLMTransportError

_PIPELINE = "api.app.run_evidence_pipeline"

client = TestClient(app, raise_server_exceptions=False)


# --- Exception handler mapping ---


@pytest.mark.parametrize("exc,expected_status,expected_type", [
    (PlannerError("planner failed"),          502, UPSTREAM_FAILURE),
    (LLMTransportError("transport failed"),   502, UPSTREAM_FAILURE),
    (RedditAuthError("reddit auth failed"),   502, UPSTREAM_FAILURE),
    (LLMStructuredOutputError("bad schema"),  500, SYNTHESIS_CONTRACT_FAILURE),
    (RuntimeError("unexpected"),              500, INTERNAL_ERROR),
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
    PlannerError("x"),
    LLMTransportError("x"),
    RedditAuthError("x"),
    LLMStructuredOutputError("x"),
    RuntimeError("x"),
])
def test_error_response_content_type(exc: Exception) -> None:
    with patch(_PIPELINE, side_effect=exc):
        response = client.post("/api/run", json={"query": "valid query"})

    assert "application/problem+json" in response.headers["content-type"]


# --- Route-level guards ---


def test_blank_query_returns_400() -> None:
    response = client.post("/api/run", json={"query": "   "})
    assert response.status_code == 400
    body = response.json()
    assert body["type"] == INVALID_REQUEST
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
