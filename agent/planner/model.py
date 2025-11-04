"""
Pydantic models for Agent Planner data structures.
"""
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

class SearchPlan(BaseModel):
    """Structured plan output from the Planner."""

    plan_id: str = Field(
        description="Unique plan identifier for traceability across planner → fetcher → filters"
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
    def validate_subreddits(cls, subreddits: list[str]) -> list[str]:
        
        """Validate and normalize subreddit names."""

        allowed = {name.lower() for name in settings.ALLOWED_SUBREDDITS}
        default = [name.lower() for name in settings.DEFAULT_SUBREDDITS]
        max_subreddit_count = settings.MAX_SUBREDDITS

        if not subreddits:
            logger.warning(f"No subreddits provided. Defaulting to {default}")
            return default[: max_subreddit_count]
        
        valid_subreddits: list[str] = []
        for raw_subreddit in subreddits: 
            if not isinstance(raw_subreddit, str):
                raise TypeError("Subreddit values must be strings")
            
            cleaned_subreddit = raw_subreddit.strip().lower().removeprefix("r/")

            if not cleaned_subreddit or cleaned_subreddit not in allowed: 
                continue 
            
            if cleaned_subreddit not in valid_subreddits: 
                valid_subreddits.append(cleaned_subreddit)
            
        if not valid_subreddits: 
            logger.warning(f"No valid subreddits found. Defaulting to {default}")
            return default[: settings.MAX_SUBREDDITS]

        if len(valid_subreddits) > settings.MAX_SUBREDDITS: 
            truncated = valid_subreddits[: settings.MAX_SUBREDDITS]
            logger.warning(f"Truncated subreddits to {truncated}")
            valid_subreddits = truncated

        return valid_subreddits
      
    @field_validator("search_terms")
    @classmethod
    def validate_search_terms(cls, search_terms: list[str]) -> list[str]:
        """
        Validate and clean search terms.
        """
        max_term_count = settings.MAX_SEARCH_TERMS
        if not search_terms:
            raise ValueError("search_terms must contain at least one term")
        
        cleaned_terms: list[str] = []
        for raw_term in search_terms:
            if not isinstance(raw_term, str):
                raise TypeError("Each search term must be a string")

            term = raw_term.strip()
            if not term:
                raise ValueError("search_terms must be non-empty strings")

            if term in cleaned_terms:
                continue

            cleaned_terms.append(term)

            if len(cleaned_terms) == max_term_count:
                logger.warning(f"Truncated search_terms to {cleaned_terms}")
                break
        return cleaned_terms

    @field_validator("plan_id")
    @classmethod
    def validate_plan_id(cls, plan_id: str) -> str:
        "Ensure plan_id is valid UUID string"
        cleaned_plan_id = plan_id.strip()
        if not cleaned_plan_id: 
            raise ValueError("plan_id cannot be empty")
        
        try: 
            UUID(cleaned_plan_id)
        except ValueError as exc: 
            raise ValueError("plan_id must be a valid UUID string") from exc
        return cleaned_plan_id
        