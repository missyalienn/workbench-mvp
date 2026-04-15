from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Research brief
# ---------------------------------------------------------------------------


class ResearchBrief(BaseModel):
    """Research contract produced by brief_generator. Drives all downstream agents."""

    project_type: str = Field(..., description="Type of renovation project, e.g. 'bathroom tile replacement'.")
    location: str | None = Field(None, description="City and state, e.g. 'Brooklyn, NY'. Required for permit routing.")
    scope_description: str = Field(..., description="Cleaned, normalized description of the project scope.")
    constraints: dict = Field(default_factory=dict, description="Sparse dict of known constraints: budget, timeline, diy_vs_contractor.")
    active_dimensions: list[str] = Field(..., description="Subset of ['permits', 'costs', 'contractors', 'materials'] relevant to this project.")
    fetch_query: str = Field(..., description="Unified broad query for the shared Reddit fetch, covering all active dimensions.")

    @field_validator("project_type", "scope_description", "fetch_query")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank or whitespace.")
        return v

    @field_validator("active_dimensions")
    @classmethod
    def dimensions_must_be_valid(cls, v: list[str]) -> list[str]:
        valid = {"permits", "costs", "contractors", "materials"}
        invalid = [d for d in v if d not in valid]
        if invalid:
            raise ValueError(f"Invalid dimensions: {invalid}. Must be subset of {valid}.")
        if not v:
            raise ValueError("active_dimensions must not be empty.")
        return v


# ---------------------------------------------------------------------------
# Agent inputs / outputs
# ---------------------------------------------------------------------------


class AgentInput(TypedDict):
    """State passed to each research agent via Send. Does not expose full GraphState."""

    brief: ResearchBrief
    reddit_posts: list[Any] | None
    dimension: str


class SourceRef(BaseModel):
    url: str
    title: str | None = None
    source: str  # "reddit" | "tavily" | "dob"


class Finding(BaseModel):
    content: str
    source: SourceRef


class FindingsBlock(BaseModel):
    """Structured research output returned by each research agent."""

    dimension: str  # "permits" | "costs" | "contractors" | "materials"

    @field_validator("dimension")
    @classmethod
    def dimension_must_be_valid(cls, v: str) -> str:
        valid = {"permits", "costs", "contractors", "materials"}
        if v not in valid:
            raise ValueError(f"Invalid dimension: {v!r}. Must be one of {valid}.")
        return v
    summary: str
    findings: list[Finding]
    gaps: list[str]
    sources: list[SourceRef]


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------


class RenovationReport(BaseModel):
    """Fixed output schema written by the synthesizer."""

    project_type: str
    location: str | None
    scope_framing: str
    permits: str | None = None
    costs: str | None = None
    contractor_insights: str | None = None
    materials_and_techniques: str | None = None
    assumptions: list[str]
    gaps: list[str]
    citations: list[SourceRef]


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


class GraphState(TypedDict):
    brief: ResearchBrief | None
    reddit_posts: list[Any] | None           # shared corpus — set by reddit_fetch_node
    findings: Annotated[list[FindingsBlock], operator.add]  # parallel-safe accumulation
    report: RenovationReport | None
