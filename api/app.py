from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent.planner.errors import PlannerError
from api.errors import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    SYNTHESIS_CONTRACT_FAILURE,
    UPSTREAM_FAILURE,
    VALIDATION_ERROR,
    ProblemDetail,
    problem_response,
)
from api.pipeline import run_evidence_pipeline
from services.reddit_client.session import RedditAuthError
from services.synthesizer.llm_execution.errors import LLMStructuredOutputError, LLMTransportError

# To start the FastAPI app, run:
# uvicorn api.app:app --reload

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


def _trace_id(request: Request) -> str | None:
    return request.headers.get("traceparent")


# --- Exception handlers ---


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem_response(
        type=VALIDATION_ERROR,
        title="Validation error",
        status=422,
        detail="Request body failed validation.",
        instance=str(request.url.path),
        trace_id=_trace_id(request),
        errors=exc.errors(),
    )


@app.exception_handler(LLMStructuredOutputError)
async def synthesis_contract_failure_handler(request: Request, exc: LLMStructuredOutputError) -> JSONResponse:
    return problem_response(
        type=SYNTHESIS_CONTRACT_FAILURE,
        title="Synthesis contract failure",
        status=500,
        detail=str(exc),
        instance=str(request.url.path),
        trace_id=_trace_id(request),
    )


@app.exception_handler(PlannerError)
async def planner_error_handler(request: Request, exc: PlannerError) -> JSONResponse:
    return problem_response(
        type=UPSTREAM_FAILURE,
        title="Upstream failure",
        status=502,
        detail=str(exc),
        instance=str(request.url.path),
        trace_id=_trace_id(request),
    )


@app.exception_handler(LLMTransportError)
async def llm_transport_error_handler(request: Request, exc: LLMTransportError) -> JSONResponse:
    return problem_response(
        type=UPSTREAM_FAILURE,
        title="Upstream failure",
        status=502,
        detail=str(exc),
        instance=str(request.url.path),
        trace_id=_trace_id(request),
    )


@app.exception_handler(RedditAuthError)
async def reddit_auth_error_handler(request: Request, exc: RedditAuthError) -> JSONResponse:
    return problem_response(
        type=UPSTREAM_FAILURE,
        title="Upstream failure",
        status=502,
        detail=str(exc),
        instance=str(request.url.path),
        trace_id=_trace_id(request),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return problem_response(
        type=INTERNAL_ERROR,
        title="Internal server error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
        trace_id=_trace_id(request),
    )


# --- Routes ---


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.post(
    "/api/run",
    responses={
        400: {"model": ProblemDetail, "description": "Blank or whitespace query"},
        422: {"model": ProblemDetail, "description": "Request validation error"},
        500: {"model": ProblemDetail, "description": "Internal server error or synthesis contract failure"},
        502: {"model": ProblemDetail, "description": "Upstream failure (planner, LLM transport, or Reddit auth)"},
    },
)
def run(body: QueryRequest, request: Request):
    if not body.query.strip():
        return problem_response(
            type=INVALID_REQUEST,
            title="Invalid request",
            status=400,
            detail="Query must not be blank or whitespace.",
            instance=str(request.url.path),
            trace_id=_trace_id(request),
        )
    return run_evidence_pipeline(body.query)
