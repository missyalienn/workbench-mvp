from __future__ import annotations

"""Configuration models for the selector component."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt


class SelectorConfig(BaseModel):
    """Runtime limits controlling selector behavior."""

    model_config = ConfigDict(extra="forbid")

    max_posts: PositiveInt = Field(..., description="Max number of posts for LLM context")
    max_comments_per_post: PositiveInt = Field(..., description="Max number of comments per post for LLM context")
    max_post_chars: PositiveInt = Field(..., description="Max number of characters allowed in post excerpt")
    max_comment_chars: PositiveInt = Field(..., description="Max number of characters allowed in comment excerpt")


__all__ = ["SelectorConfig"]
