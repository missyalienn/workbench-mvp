from __future__ import annotations

"""Configuration models for the curator component."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt


class SummarizerConfig(BaseModel):
    """Runtime limits for curation behavior."""

    model_config = ConfigDict(extra="forbid")

    summary_char_budget: PositiveInt = Field(..., description="Maximum allowed characters in the summary")
    max_highlights: PositiveInt = Field(..., description="Maximum highlight items permitted")
    max_cautions: PositiveInt = Field(..., description="Maximum caution items permitted")


__all__ = ["SummarizerConfig"]
