from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from api.errors import (
    EXTERNAL_SERVICE_FAILURE,
    INTERNAL_SERVER_ERROR,
    VALIDATION_ERROR,
    DETAIL_EXTERNAL_SERVICE_FAILURE,
    DETAIL_INTERNAL_SERVER_ERROR,
    DETAIL_VALIDATION_ERROR,
    ProblemDetail,
    problem_response,
)
from api.pipeline import run_evidence_pipeline
from common.exceptions import ExternalServiceError
from config.logging_config import configure_logging, get_logger

# To start the FastAPI app, run:
# uvicorn api.app:app --reload

configure_logging()
logger = get_logger(__name__)

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

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query must not be blank or whitespace.")
        return v


def _trace_id(request: Request) -> str | None:
    return request.headers.get("traceparent")


# --- Exception handlers ---


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem_response(
        type=VALIDATION_ERROR,
        title="Validation error",
        status=422,
        detail=DETAIL_VALIDATION_ERROR,
        instance=str(request.url.path),
        trace_id=_trace_id(request),
        errors=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(ExternalServiceError)
async def external_service_error_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
    logger.warning(
        "api.external_service_failure",
        exc_type=type(exc).__name__,
        exc=str(exc),
        path=str(request.url.path),
        trace_id=_trace_id(request),
    )
    return problem_response(
        type=EXTERNAL_SERVICE_FAILURE,
        title="External service failure",
        status=502,
        detail=DETAIL_EXTERNAL_SERVICE_FAILURE,
        instance=str(request.url.path),
        trace_id=_trace_id(request),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "api.unhandled_exception",
        exc_type=type(exc).__name__,
        exc=str(exc),
        path=str(request.url.path),
        trace_id=_trace_id(request),
    )
    return problem_response(
        type=INTERNAL_SERVER_ERROR,
        title="Internal server error",
        status=500,
        detail=DETAIL_INTERNAL_SERVER_ERROR,
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
        422: {"model": ProblemDetail, "description": "Request validation error"},
        500: {"model": ProblemDetail, "description": "Internal server error"},
        502: {"model": ProblemDetail, "description": "External service failure"},
    },
)
def run(body: QueryRequest, request: Request):
    return run_evidence_pipeline(body.query)
