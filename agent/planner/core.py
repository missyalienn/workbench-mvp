"""
Core planner logic with single LLM call.
"""

from .model import SearchPlan
from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from config.logging_config import get_logger
from services.ingestion.openai_client import get_openai_client

logger = get_logger(__name__)


def create_search_plan(user_query: str) -> SearchPlan:
    """
    Generate a structured search plan from a user query.

    Args:
        user_query: User's question or topic (e.g., "How do I fix a leaky faucet?")

    Returns:
        SearchPlan: Pydantic model with plan_id, search_terms, subreddits, and notes

    Raises:
        ValueError: If user_query is empty or invalid
        RuntimeError: If LLM call fails or returns invalid structure

    Implementation:
    - Generate unique plan_id using uuid.uuid4()
    - Call OpenAI with structured output mode
    - Parse response into SearchPlan model
    - Validate and return

    Logging Strategy:
    - logger.info() for high-level events (query received, plan generated with plan_id)
    - logger.debug() for detailed reasoning (full plan contents, LLM response details)
    - logger.warning() for adjustments (truncating subreddit list, fallback behavior)
    - logger.error() for failures (validation errors, LLM call failures)
    """
    # TODO: Validate user_query is non-empty
    # TODO: Log query received at INFO level
    # TODO: Generate unique plan_id using uuid.uuid4()
    # TODO: Get OpenAI client using get_openai_client()
    # TODO: Format user message using USER_PROMPT_TEMPLATE
    # TODO: Call OpenAI API with JSON mode or structured output
    # TODO: Parse LLM response into dict
    # TODO: Add plan_id to response dict
    # TODO: Create SearchPlan from response (validates via Pydantic)
    # TODO: Log successful plan generation at INFO level with plan_id
    # TODO: Log full plan details at DEBUG level
    # TODO: Return validated SearchPlan
    # TODO: Handle exceptions with appropriate error logging
    pass

