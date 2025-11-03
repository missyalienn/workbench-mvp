"""
Pydantic models for Agent Planner data structures.
"""

from pydantic import BaseModel, Field, field_validator


class SearchPlan(BaseModel):
    """Structured plan output from the Planner."""

    plan_id: str = Field(
        description="Unique identifier for traceability across planner → fetcher → filters"
    )
    search_terms: list[str] = Field(
        description="List of search terms to query Reddit (e.g., ['deck repair', 'wood stain'])"
    )
    subreddits: list[str] = Field(
        description="List of subreddit names without 'r/' prefix (e.g., ['diy', 'homeimprovement'])"
    )
    notes: str = Field(
        description="Brief reasoning or context about the search plan"
    )

    @field_validator("subreddits")
    @classmethod
    def validate_subreddits(cls, v: list[str]) -> list[str]:
        """
        Validate subreddit list meets requirements.

        Rules:
        - Must contain 1-3 subreddits from allowed set
        - Truncate to 3 if more provided
        - Never return empty list

        TODO: Implement validation logic
        TODO: Add logging for warnings (truncation, invalid subreddits)
        """
        pass

    @field_validator("search_terms")
    @classmethod
    def validate_search_terms(cls, v: list[str]) -> list[str]:
        """
        Validate search terms are non-empty.

        Rules:
        - Must be non-empty list
        - Each term should be non-empty string

        TODO: Implement validation logic
        """
        pass

    @field_validator("plan_id")
    @classmethod
    def validate_plan_id(cls, v: str) -> str:
        """
        Validate plan_id is non-empty.

        TODO: Implement validation logic
        """
        pass

