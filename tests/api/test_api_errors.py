"""Unit tests for api.errors."""

from __future__ import annotations

import json

from api.errors import EXTERNAL_SERVICE_FAILURE, problem_response


def test_problem_response_shape() -> None:
    response = problem_response(
        type=EXTERNAL_SERVICE_FAILURE,
        title="Upstream failure",
        status=502,
        detail="Something went wrong.",
        instance="/api/run",
    )
    data = json.loads(response.body)
    assert data["type"] == EXTERNAL_SERVICE_FAILURE
    assert data["title"] == "Upstream failure"
    assert data["status"] == 502
    assert data["detail"] == "Something went wrong."
    assert data["instance"] == "/api/run"


def test_problem_response_status_code() -> None:
    response = problem_response(
        type=EXTERNAL_SERVICE_FAILURE,
        title="Upstream failure",
        status=502,
        detail="Something went wrong.",
        instance="/api/run",
    )
    assert response.status_code == 502


def test_problem_response_media_type() -> None:
    response = problem_response(
        type=EXTERNAL_SERVICE_FAILURE,
        title="Upstream failure",
        status=502,
        detail="Something went wrong.",
        instance="/api/run",
    )
    assert response.media_type == "application/problem+json"


def test_problem_response_omits_trace_id_when_none() -> None:
    response = problem_response(
        type=EXTERNAL_SERVICE_FAILURE,
        title="Upstream failure",
        status=502,
        detail="Something went wrong.",
        instance="/api/run",
    )
    data = json.loads(response.body)
    assert "trace_id" not in data


def test_problem_response_includes_trace_id_when_present() -> None:
    response = problem_response(
        type=EXTERNAL_SERVICE_FAILURE,
        title="Upstream failure",
        status=502,
        detail="Something went wrong.",
        instance="/api/run",
        trace_id="00-abc123-def456-01",
    )
    data = json.loads(response.body)
    assert data["trace_id"] == "00-abc123-def456-01"
