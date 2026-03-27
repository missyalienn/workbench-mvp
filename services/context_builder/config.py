from __future__ import annotations

"""Configuration models for the context_builder component."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt


class ContextBuilderConfig(BaseModel):
    """Runtime limits controlling context builder behavior."""

    model_config = ConfigDict(extra="forbid")

    max_posts: PositiveInt = Field(..., description="Max number of posts for LLM context")
    max_comments_per_post: PositiveInt = Field(..., description="Max number of comments per post for LLM context")
    max_post_chars: PositiveInt = Field(..., description="Max number of characters allowed in post excerpt")
    max_comment_chars: PositiveInt = Field(..., description="Max number of characters allowed in comment excerpt")


__all__ = ["ContextBuilderConfig"]
