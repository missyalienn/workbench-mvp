"""RFC 9457 Problem Details for HTTP APIs.

Provides a typed ProblemDetail model, problem type URI constants, and a
problem_response() helper for returning application/problem+json responses.
"""

from __future__ import annotations

from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Problem type URIs
INVALID_REQUEST = "/problems/invalid-request"
VALIDATION_ERROR = "/problems/validation-error"
SYNTHESIS_CONTRACT_FAILURE = "/problems/synthesis-contract-failure"
UPSTREAM_FAILURE = "/problems/upstream-failure"
INTERNAL_ERROR = "/problems/internal-error"


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


def problem_response(
    *,
    type: str,
    title: str,
    status: int,
    detail: str,
    instance: str,
    trace_id: str | None = None,
) -> JSONResponse:
    """Return an application/problem+json response."""
    body = ProblemDetail(
        type=type,
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        trace_id=trace_id,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
