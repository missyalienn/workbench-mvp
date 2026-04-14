# Error Handling

## Overview

This document describes the error handling design for the Workbench API. The system uses typed internal exceptions at service boundaries, FastAPI exception handlers for HTTP translation, and RFC 9457 Problem Details for all error responses.

The central rule: **exception taxonomy is defined by failure category, not by which service raised the error.**

---

## Design Principles

- Exception types express what kind of failure occurred, not where in the codebase it happened.
- Services raise typed exceptions. The API layer translates them to HTTP. These are separate concerns.
- No raw tracebacks or internal error details are exposed to clients.
- All error responses use `application/problem+json` (RFC 9457).
- Logging happens at the raise site (service layer). Exception handlers add request-level context.
- Handler count maps to distinct HTTP behaviors, not to exception class count.

---

## Error Categories

| Category | Description | HTTP Status |
|---|---|---|
| Request validation | Malformed or invalid request body | 422 |
| External service failure | Auth, rate limit, timeout, or bad response from a dependency | 502 |
| Internal processing failure | Unexpected error within this service | 500 |

---

## HTTP Status Mapping

| Status | Meaning in this API |
|---|---|
| 422 | Request failed FastAPI/Pydantic validation |
| 502 | An external service (OpenAI, Reddit) failed to fulfill the request |
| 500 | Unexpected internal error — a bug or unhandled condition |

**Note:** 429 from an external service is not forwarded to the client. Retries are handled internally (see [Retry Behavior](#retry-behavior)). If retries are exhausted, the client receives 502.

---

## Internal Exception Taxonomy

```
Exception
├── ExternalServiceError          # base: any external dependency failure → 502
│   ├── AuthError                 # authentication/authorization failure
│   ├── RateLimitError            # rate limit exhausted after retries
│   ├── ExternalTimeoutError      # timeout after retries
│   └── InvalidResponseError             # invalid, unparseable, or contract-violating response
└── (all others)                  # caught by catch-all handler → 500
```

Defined in `common/exceptions.py`. Imported by service modules and the API layer.

**What belongs under `ExternalServiceError`:**
- Reddit OAuth failure → `AuthError`
- Reddit 429 after retry exhaustion → `RateLimitError`
- OpenAI network timeout after retries → `ExternalTimeoutError`
- OpenAI returned invalid JSON or failed schema validation → `InvalidResponseError`
- OpenAI `output_parsed` is `None` → `InvalidResponseError`

**What does not belong under `ExternalServiceError`:**
- Pydantic validation on incoming request body — handled by FastAPI as `RequestValidationError`
- Unexpected programmer errors — caught by the catch-all `Exception` handler

---

## Exception → HTTP Mapping

| Exception | HTTP Status | Problem Type URI |
|---|---|---|
| `RequestValidationError` (FastAPI) | 422 | `/problems/validation-error` |
| `ExternalServiceError` (and subclasses) | 502 | `/problems/external-service-failure` |
| `Exception` (catch-all) | 500 | `/problems/internal-server-error` |

---

## Request Flow Example — Rate Limit

```
Client → POST /api/run
  │
  ├── FastAPI validates request body (Pydantic)
  │     └── blank query → RequestValidationError → 422
  │
  ├── pipeline.py calls reddit fetcher
  │     └── tenacity retries on 429 (exponential backoff)
  │           └── retries exhausted → raises RateLimitError
  │
  └── FastAPI ExternalServiceError handler
        ├── logger.warning("api.external_service_failure", ...)
        └── returns 502 application/problem+json
```

---

## FastAPI Handler Design

Three handlers cover all cases:

```python
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    # 422 — framework validation failure
    ...

@app.exception_handler(ExternalServiceError)
async def external_service_error_handler(request, exc):
    # 502 — any external dependency failure
    logger.warning(
        "api.external_service_failure",
        exc_type=type(exc).__name__,
        exc=str(exc),
        path=str(request.url.path),
        trace_id=_trace_id(request),
    )
    return problem_response(type=EXTERNAL_SERVICE_FAILURE, status=502, ...)

@app.exception_handler(Exception)
async def internal_error_handler(request, exc):
    # 500 — unexpected / unhandled
    logger.exception(
        "api.unhandled_exception",
        exc_type=type(exc).__name__,
        exc=str(exc),
        path=str(request.url.path),
    )
    return problem_response(type=INTERNAL_SERVER_ERROR, status=500, ...)
```

`exc_info=True` on the catch-all attaches the full stack trace to the log event.

---

## Logging & Observability

Two log events occur per handled external failure:

**1. Service layer — at the raise site:**
```json
{
  "event": "synthesizer.failed",
  "level": "error",
  "exc_type": "AuthenticationError",
  "exc": "Invalid API key",
  "model": "gpt-4.1-mini",
  "plan_id": "a3f9..."
}
```

**2. API layer — in the exception handler:**
```json
{
  "event": "api.external_service_failure",
  "level": "warning",
  "exc_type": "AuthError",
  "exc": "OpenAI authentication failed",
  "path": "/api/run",
  "trace_id": "00-abc123-def456-01"
}
```

Together these give full context: what failed, in which service, during which plan, on which request.

**Client response — detail field:** Always a generic, stable message. Never `str(exc)`. Internal error messages are for logs only. Detail strings are defined as constants in `api/errors.py` alongside the problem type URIs — not as inline literals in handlers.

```json
{
  "type": "/problems/external-service-failure",
  "title": "External service failure",
  "status": 502,
  "detail": "An external service failed to fulfill the request.",
  "instance": "/api/run",
  "trace_id": "00-abc123-def456-01"
}
```

The `trace_id` (forwarded from the `traceparent` request header) is the correlation key between client-facing errors and internal logs.

---

## Retry Behavior

Retries are handled at the transport layer using `tenacity`. Each client defines its own `is_retryable` predicate and calls `build_retry()` from `services/http/retry_policy.py`.

| Condition | Retried | Exception raised on exhaustion |
|---|---|---|
| `Timeout`, `ConnectionError` | Yes | `TimeoutError` |
| HTTP 429 | Yes | `RateLimitError` |
| HTTP 500, 502, 503, 504 | Yes | `InvalidResponseError` |
| HTTP 4xx (other than 429) | No | re-raised immediately |
| Auth failure | No | `AuthError` |
| Timeout / ConnectionError | Yes | `ExternalTimeoutError` |

Retry settings (max attempts, wait multiplier, max wait) are configured in `config/settings.py`.

**The 429 rule:** A 429 from an external service is an implementation detail. It is retried internally. If retries are exhausted, the client receives 502 — never 429. The client should not need to know which upstream rate-limited us.

---

## Use of HTTPException

`HTTPException` is not used in this codebase for application errors. All error responses go through the `problem_response()` helper to ensure consistent `application/problem+json` formatting.

`HTTPException` is appropriate only for framework-level concerns (e.g., authentication middleware). Do not use it in route handlers or service code.

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Exception classes | `PascalCase`, named by failure category | `AuthError`, `ExternalTimeoutError` |
| Problem type URIs | kebab-case path | `/problems/external-service-failure` |
| Log event keys | `service.event` | `api.unhandled_exception`, `synthesizer.failed` |
| `exc_type` log field | `type(exc).__name__` | `"AuthenticationError"` |
| `detail` in API response | Generic, stable string | `"An external service failed to fulfill the request."` |

---

## Anti-Patterns

**Do not** name exceptions after the service that raised them (`PlannerError`, `RedditAuthError`). If the planner and the synthesizer both fail due to an auth error, both should raise `AuthError`. The service name belongs in the log, not the exception class.

**Do not** use `str(exc)` as the `detail` field in error responses. This leaks internal error messages to clients.

**Do not** catch exceptions in route handlers and return inline `problem_response()` calls. All error translation belongs in exception handlers.

**Do not** use `HTTPException` for domain or service errors.

**Do not** add a new exception class per service. The taxonomy is flat and categorical: `AuthError`, `RateLimitError`, `TimeoutError`, `InvalidResponseError`. A new class is only justified if it maps to a distinct HTTP behavior.

**Do not** leave the catch-all `Exception` handler silent. It must log with `exc_info=True`.
