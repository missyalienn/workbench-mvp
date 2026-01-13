"""Data contracts for the curator input layer."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pydantic.types import PositiveInt

class PostPayload(BaseModel):
    """Compact representation of a Reddit post passed to the curator."""

    model_config = ConfigDict(extra="forbid")

    post_id: str = Field(..., description="Reddit post ID")
    subreddit: str = Field(..., description="Source subreddit (e.g., diy)")
    title: str = Field(..., description="Cleaned Reddit post title")
    url: str = Field(..., description="Canonical Reddit permalink")
    body_excerpt: str = Field(..., description="Truncated body text shown to the LLM")
    top_comment_excerpts: list[str] = Field(
        default_factory=list,
        description="Truncated comment excerpts selected for this post",
    )
    post_karma: int = Field(..., description="Native Reddit score (upvotes - downvotes)")
    num_comments: int = Field(..., description="Number of comments accepted by the fetcher for this post")
    relevance_score: float = Field(..., description="Fetcher-assigned relevance score")
    matched_keywords: list[str] = Field(
        default_factory=list,
        description="Fetcher keyword matches used in scoring",
    )


class SummarizeRequest(BaseModel):
    """Input contract consumed by the curator/LLM layer."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="Original user question")
    plan_id: UUID = Field(..., description="Planner-generated ID for this fetch run")
    post_payloads: list[PostPayload] = Field(
        ...,
        description="Selected Reddit posts with trimmed content for the LLM context",
    )
    prompt_version: str = Field(..., description="Version identifier for the prompt template")
    max_posts: int = Field(..., description="Cap on posts included in this request")
    max_comments_per_post: int = Field(..., description="Cap on comment excerpts per post")
    max_post_chars: PositiveInt = Field(..., description="Max characters allocated to each post body excerpt")
    max_comment_chars: PositiveInt = Field(..., description="Max characters allocated to each comment excerpt")
    summary_char_budget: PositiveInt = Field(..., description="Max characters allowed in the generated summary")
    max_highlights: PositiveInt = Field(..., description="Max number of highlight bullets permitted")
    max_cautions: PositiveInt = Field(..., description="Max number of caution bullets permitted")


class ThreadEvidence(BaseModel):
    """Ranked Reddit thread selected as evidence for the user's query."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., description="Rank of the thread in the curation result")
    post_id: str = Field(..., description="Reddit post ID backing this claim")
    title: str = Field(..., description="Reddit post title")
    subreddit: str = Field(..., description="Result subreddit")
    url: str = Field(..., description="Canonical Reddit permalink")
    relevance_score: float = Field(..., description="Fetcher-assigned relevance score")


class CurationResult(BaseModel):
    """Evidence-first research payload listing the most relevant threads."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "partial", "error"] = Field(
        ...,
        description="Overall health of the curation attempt",
    )
    threads: list[ThreadEvidence] = Field(
        ...,
        description="Ranked Reddit threads selected for the query",
    )
    limitations: list[str] = Field(
        ...,
        description="Reasons evidence is thin or no threads were selected",
    )
    prompt_version: str = Field(
        ...,
        description="Prompt template version used for this run",
    )

__all__ = ["PostPayload", "SummarizeRequest", "ThreadEvidence", "CurationResult"]
