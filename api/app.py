from api.pipeline import run_evidence_pipeline

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/api/run")
def run(body: QueryRequest):
    return run_evidence_pipeline(body.query)

