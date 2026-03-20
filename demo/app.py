import time

from demo.pipeline import run_evidence_pipeline

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.logging_config import get_logger
from services.observability.run_context import elapsed_ms, generate_run_id, sanitize_query

# To start the FastAPI app, run:
# uvicorn demo.app:app --reload

logger = get_logger(__name__)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DemoQueryRequest(BaseModel):
    query: str


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.post("/api/demo")
def run_demo(body: DemoQueryRequest):
    run_id = generate_run_id()
    safe_query = sanitize_query(body.query)
    request_start = time.perf_counter()
    logger.info(
        "stage=request_start event=start run_id=%s status=ok query=%s",
        run_id,
        safe_query,
    )
    payload = run_evidence_pipeline(body.query, run_id=run_id)
    logger.info(
        "stage=request_end event=end run_id=%s status=ok duration_ms=%d",
        run_id,
        elapsed_ms(request_start),
    )
    return payload
