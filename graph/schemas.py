"""Domain schemas for the V2 due diligence graph.

These are the core data contracts shared across graph nodes, agents, and the
final report. No city-specific identifiers appear here.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

VALID_DIMENSIONS = {"permits", "violations", "liens", "zoning", "ownership"}


class SourceRef(BaseModel):
    title: str = Field(description="Human-readable name for the source or dataset")
    url: str | None = Field(default=None, description="URL if web-accessible")
    dataset: str | None = Field(
        default=None,
        description="Dataset name as returned by the municipal data client (e.g. 'DOB Permit Issuance')",
    )


class Finding(BaseModel):
    description: str = Field(description="Plain-language description of the finding")
    # TODO: revisit once #128 confirms Socrata date format — may warrant datetime + field_validator
    date: str | None = Field(default=None, description="Date string as returned by the data source")
    status: str | None = Field(default=None, description="Status string as returned by the data source")
    source: SourceRef | None = Field(default=None, description="Data source for this finding")


class FindingsBlock(BaseModel):
    dimension: Literal["permits", "violations", "liens", "zoning", "ownership"] = Field(
        description="Due diligence dimension this block covers"
    )
    summary: str = Field(description="Narrative summary of findings for this dimension")
    findings: list[Finding] = Field(
        default_factory=list, description="Individual findings returned by the agent"
    )
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Plain-language risk signals (e.g. '3 open violations', 'lien on file')",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Data gaps or queries that returned no results",
    )
    sources: list[SourceRef] = Field(
        default_factory=list, description="All sources consulted for this dimension"
    )


class DueDiligenceRequest(BaseModel):
    query_type: Literal["address_lookup", "research_task"] = Field(
        description="Whether the query is an address lookup or an open research task"
    )
    raw_query: str = Field(description="Preserved original user input")
    address: str | None = Field(
        default=None, description="Normalized address — populated for address_lookup"
    )
    city: str | None = Field(default=None, description="Normalized city name")
    state: str | None = Field(default=None, description="Two-letter state code")
    # City-specific sub-unit (e.g. borough, county) — populated by GeocodingClient if
    # relevant; never referenced by name in agent logic.
    subdivision: str | None = Field(
        default=None,
        description="Optional city-specific sub-unit (e.g. borough); populated by geocoding layer",
    )
    # City-specific unique property identifier resolved by GeocodingClient
    # (e.g. BBL in NYC, PIN in Chicago, APN elsewhere).
    parcel_id: str | None = Field(
        default=None,
        description="City-specific unique property identifier resolved by GeocodingClient",
    )
    research_question: str | None = Field(
        default=None, description="Populated for research_task queries"
    )
    investor_context: Literal["pre-acquisition", "portfolio review"] | None = Field(
        default=None, description="Optional investor intent context"
    )
    active_dimensions: list[str] = Field(
        default_factory=list,
        description="Subset of due diligence dimensions to research: permits, violations, liens, zoning, ownership",
    )

    @field_validator("active_dimensions")
    @classmethod
    def validate_active_dimensions(cls, dims: list[str]) -> list[str]:
        invalid = [d for d in dims if d not in VALID_DIMENSIONS]
        if invalid:
            raise ValueError(
                f"Invalid dimensions: {invalid}. Must be subset of {sorted(VALID_DIMENSIONS)}"
            )
        return dims

    @field_validator("state")
    @classmethod
    def normalize_state(cls, state: str | None) -> str | None:
        if state is not None:
            return state.strip().upper()
        return state


class DueDiligenceReport(BaseModel):
    address: str | None = Field(default=None, description="None for research_task queries")
    parcel_id: str | None = Field(default=None, description="None for research_task queries")
    city: str = Field(description="City where the property or research is located")
    research_question: str | None = Field(
        default=None, description="Populated for research_task queries"
    )
    generated_at: datetime = Field(description="Timestamp when the report was generated")

    # Per-dimension summaries — None if dimension not in active_dimensions or agent failed
    permit_summary: str | None = Field(default=None)
    violation_summary: str | None = Field(default=None)
    lien_summary: str | None = Field(default=None)
    zoning_summary: str | None = Field(default=None)
    ownership_summary: str | None = Field(default=None)

    # Structured risk signals — None if dimension not run or agent failed
    open_permit_count: int | None = Field(default=None)
    open_violation_count: int | None = Field(default=None)
    active_lien_count: int | None = Field(default=None)
    tax_delinquent: bool | None = Field(default=None)
    ownership_transfers_last_5yr: int | None = Field(default=None)

    # Synthesized output
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Plain-language risk signals aggregated across all dimensions",
    )
    # "LOW" | "MEDIUM" | "HIGH" for address_lookup; None for research_task
    risk_score: Literal["LOW", "MEDIUM", "HIGH"] | None = Field(
        default=None,
        description="LLM-assigned risk score for address_lookup queries; None for research_task",
    )
    recommendation: str = Field(
        description="Narrative synthesis — always populated; notes missing dimensions"
    )

    # Full findings for drill-down
    findings: list[FindingsBlock] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
