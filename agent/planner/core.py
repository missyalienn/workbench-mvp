"""
Core planner logic with single LLM call.
"""

import json
from uuid import uuid4
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
    # Validate user_query is non-empty
    if not user_query or not user_query.strip():
        logger.error("Empty user_query provided")
        raise ValueError("user_query cannot be empty")
    
    logger.info(f"Received query: {user_query}")
    
    # Generate unique plan_id
    plan_id = str(uuid4())
    logger.debug(f"Generated plan_id: {plan_id}")
    
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Format user message
        user_message = USER_PROMPT_TEMPLATE.format(user_query=user_query)
        
        # Call OpenAI API with JSON mode
        logger.debug("Calling OpenAI API for search plan generation")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse LLM response
        raw_content = response.choices[0].message.content
        logger.debug(f"LLM response: {raw_content}")
        
        response_dict = json.loads(raw_content)
        
        # Add plan_id to response dict
        response_dict["plan_id"] = plan_id
        
        # Create SearchPlan (Pydantic validates)
        plan = SearchPlan(**response_dict)
        
        logger.info(f"Plan generated successfully [plan_id={plan.plan_id}]")
        logger.debug(f"Full plan: search_terms={plan.search_terms}, subreddits={plan.subreddits}, notes={plan.notes}")
        
        return plan
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise RuntimeError(f"Invalid JSON response from LLM: {e}") from e
    except Exception as e:
        logger.error(f"Failed to generate search plan: {e}")
        raise RuntimeError(f"Search plan generation failed: {e}") from e

