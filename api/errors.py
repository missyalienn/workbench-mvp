"""RFC 9457 Problem Details for HTTP APIs.

Provides a typed ProblemDetail model, problem type URI constants, and a
problem_response() helper for returning application/problem+json responses.
"""

from __future__ import annotations

from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Problem type URIs
VALIDATION_ERROR = "/problems/validation-error"
EXTERNAL_SERVICE_FAILURE = "/problems/external-service-failure"
INTERNAL_SERVER_ERROR = "/problems/internal-server-error"
PLANNER_ERROR = "/problems/planner-error"

# Response detail strings — use these constants in handlers, not inline literals
DETAIL_VALIDATION_ERROR = "Request body failed validation."
DETAIL_EXTERNAL_SERVICE_FAILURE = "An external service failed to fulfill the request."
DETAIL_INTERNAL_SERVER_ERROR = "An unexpected error occurred."
DETAIL_PLANNER_ERROR = "That doesn't look like a searchable topic. Try a question or subject you'd like to research."


class ProblemDetail(BaseModel):
    """RFC 9457 problem details response body.

    Attributes:
        type: URI identifying the problem type.
        title: Short human-readable summary of the problem type.
        status: HTTP status code.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI identifying this specific occurrence (typically the request path).
        trace_id: Forwarded traceparent header value, if present.
    """

    type: str
    title: str
    status: int
    detail: str
    instance: str
    trace_id: str | None = None
    errors: list[dict] | None = None


def problem_response(
    *,
    type: str,
    title: str,
    status: int,
    detail: str,
    instance: str,
    trace_id: str | None = None,
    errors: list[dict] | None = None,
) -> JSONResponse:
    """Return an application/problem+json response."""
    body = ProblemDetail(
        type=type,
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        trace_id=trace_id,
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
