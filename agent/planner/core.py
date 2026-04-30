"""
Core planner logic with single LLM call.
"""

import json
import time
from uuid import uuid4

from pydantic import ValidationError

from .model import SearchPlan
from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from config.logging_config import get_logger, plan_context_scope
from agent.clients.openai_client import get_openai_client, translate_openai_error
from common.exceptions import PlannerError

logger = get_logger(__name__)


def create_search_plan(user_query: str, model: str = "gpt-4.1-mini") -> SearchPlan:
    """
    Generate a structured search plan from a user query.

    Args:
        user_query: User's question or topic (e.g., "How do I fix a leaky faucet?")

    Returns:
        SearchPlan: Pydantic model with plan_id, search_terms, subreddits, and notes

    Raises:
        ValueError: If user_query is empty or invalid
        PlannerError: If the LLM call fails or returns invalid structure

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
        logger.error("planner.invalid_query", reason="empty")
        raise ValueError("user_query cannot be empty")

    # Generate unique plan_id
    plan_id = uuid4()
    plan_id_str = str(plan_id)

    # Credential failure escapes unwrapped — config error, not a planner failure
    client = get_openai_client()

    # Wrap all operations in plan_id context for traceability
    with plan_context_scope(plan_id_str):
        t0 = time.monotonic()
        logger.info("planner.start", query=user_query)
        logger.debug("planner.plan_id_generated", plan_id=plan_id_str)

        try:
            # Format user message
            user_message = USER_PROMPT_TEMPLATE.format(user_query=user_query)

            # Call OpenAI API with JSON mode
            logger.debug("planner.llm_call_start", model=model)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )

            # Parse LLM response
            raw_content = response.choices[0].message.content
            if raw_content is None:
                logger.error("planner.failed", elapsed_ms=int((time.monotonic() - t0) * 1000), error="OpenAI returned no content")
                raise InvalidResponseError("OpenAI returned no content")
            logger.debug("planner.llm_response_received", raw_content=raw_content)

            response_dict = json.loads(raw_content)

            # Add plan_id to response dict
            response_dict["plan_id"] = plan_id_str

            # Create SearchPlan (Pydantic validates)
            plan = SearchPlan(query=user_query, **response_dict)

            logger.info("planner.complete", elapsed_ms=int((time.monotonic() - t0) * 1000), n_terms=len(plan.search_terms), n_subreddits=len(plan.subreddits), search_terms=plan.search_terms, subreddits=plan.subreddits)

            return plan

        except ValidationError as e:
            logger.error("planner.failed", elapsed_ms=int((time.monotonic() - t0) * 1000), error=str(e), exc_type=type(e).__name__)
            raise PlannerError("Query could not be planned") from e
        except Exception as e:
            logger.error("planner.failed", elapsed_ms=int((time.monotonic() - t0) * 1000), error=str(e), exc_type=type(e).__name__)
            raise translate_openai_error(e) from e
