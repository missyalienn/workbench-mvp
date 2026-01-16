from demo.pipeline import run_evidence_pipeline

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class DemoQueryRequest(BaseModel):
    query: str


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/api/demo")
def run_demo(body: DemoQueryRequest):
    return run_evidence_pipeline(body.query)
