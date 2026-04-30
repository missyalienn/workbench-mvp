"""Client-facing API response models.

These are the stable public contracts between the backend and any client.
Internal pipeline fields (post_id, relevance_score, prompt_version) are
excluded here — they live in services/synthesizer/models.py.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SearchPlan(BaseModel):
    search_terms: list[str]
    subreddits: list[str]


class ClientThread(BaseModel):
    rank: int
    title: str
    subreddit: str
    url: str
    relevance_score: float


class EvidenceResponse(BaseModel):
    search_plan: SearchPlan
    status: Literal["ok", "partial", "insufficient"]
    summary: str
    threads: list[ClientThread]
    limitations: list[str]
