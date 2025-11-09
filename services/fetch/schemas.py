"""Pydantic models for RedditFetcher results.

Example:
    fetch_result = FetchResult(
        query="What's the best way to stain a pine bookshelf evenly?",
        plan_id=UUID("6751f2ae-d9e7-47f4-b439-93648bf08b5b"),
        search_terms=[
            "stain pine bookshelf",
            "even stain application",
            "best stain technique pine",
        ],
        subreddits=["woodworking"],
        fetched_at=1715208123.0,
        posts=[],
    )
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Post(BaseModel):
    """Reddit post enriched with instructional metadata and comments."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Reddit post ID (submission.id)")
    title: str = Field(..., description="Cleaned post title")
    selftext: str = Field(..., description="Cleaned body text of the post")
    post_karma: int = Field(
        ..., description="Native Reddit score (upvotes - downvotes)"
    )
    relevance_score: float = Field(
        ..., description="Keyword weighting score computed by RedditFetcher"
    )
    matched_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that contributed to the relevance score",
    )
    url: str = Field(..., description="Full Reddit permalink")
    comments: list["Comment"] = Field(
        default_factory=list,
        description="Top-level comments meeting quality thresholds",
    )
    fetched_at: float = Field(
        ..., description="UTC timestamp when the post was fetched"
    )
    source: Literal["reddit"] = Field(
        default="reddit", description="Data origin identifier"
    )


class Comment(BaseModel):
    """Top-level Reddit comment fetched by RedditFetcher."""

    model_config = ConfigDict(extra="forbid")

    comment_id: str = Field(..., description="Reddit comment ID (submission.id)")
    body: str = Field(..., description="Cleaned comment text")
    comment_karma: int = Field(..., description="Comment score (quality signal)")
    fetched_at: float = Field(..., description="UTC timestamp when the post was fetched")
    source: Literal["reddit"] = Field(
        default="reddit", description="Data origin identifier"
    )

# TO DO: 
# Add a plan_id field to the Comment object.
# Add a post_id field to the Comment object.
# Add a fetched_at field to the Comment object.


class FetchResult(BaseModel):
    """Aggregate container for Reddit posts and planner metadata."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ..., description="Original user query driving the planner search"
    )
    plan_id: UUID = Field(..., description="Identifier for the originating SearchPlan")
    search_terms: list[str] = Field(
        default_factory=list, description="Terms used to query Reddit"
    )
    subreddits: list[str] = Field(
        default_factory=list, description="Targeted subreddits"
    )
    source: Literal["reddit"] = Field(
        default="reddit", description="Data origin identifier"
    )
    fetched_at: float = Field(
        ...,
        description="UTC timestamp when the fetch occurred",
    )
    posts: list[Post] = Field(
        default_factory=list,
        description="Structured Reddit posts ready for synthesis",
    )
