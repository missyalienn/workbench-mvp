
# Planner Module Implementation Plan

## Overview

Create a clean, modular Planner that transforms user queries into structured search plans consumable by existing `services/ingestion` logic. Portfolio-grade architecture with Pydantic models and proper separation of concerns. The Planner is a reasoning layer that generates plans; downstream components handle fetching, batching, and rate limiting.

## File Structure

### 1. `agent/models.py`

Pydantic models for type-safe data structures.

**Classes:**

```python
from pydantic import BaseModel, Field

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
```

**Validation:**

- `plan_id` must be unique (use UUID or timestamp-based ID)
- `subreddits` must contain 1-3 subreddits from: {"diy", "homeimprovement", "woodworking"}
- Dynamic selection based on query intent:
                                - General/ambiguous queries (e.g., "fix door hinge") → default to including "diy"
                                - Specific queries (e.g., "refinishing table", "installing drywall") → prefer most relevant subreddit(s), may omit "diy"
- Never return empty list (fail fast if validation fails)
- Truncate to 3 max if LLM returns more; log warning
- `search_terms` must be non-empty list

**Logging for validation:**

- DEBUG: reasoning about subreddit selection, plan_id generated
- INFO: successful plan generation with plan_id
- WARNING: adjustments made (e.g., truncating subreddit list)
- ERROR: validation failures or empty results

---

### 2. `agent/planner/__init__.py`

Public API exports for the planner subpackage.

```python
from agent.planner.core import create_search_plan
from agent.models import SearchPlan

__all__ = ["create_search_plan", "SearchPlan"]
```

---

### 3. `agent/planner/core.py`

Core planner logic with single LLM call.

**Functions:**

```python
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
    """
```

**Implementation notes:**

- Import `get_openai_client()` from `services.ingestion.openai_client` (absolute import)
- Import `configure_logging()` and `get_logger()` from `config.logging_config`
- No global imports - all imports must be explicit and Pythonic
- Generate unique `plan_id` using `uuid.uuid4()` or timestamp
- Use OpenAI's JSON mode or structured output with response format
- Logging strategy:
                                - `logger.info()` for high-level events (query received, plan generated successfully with plan_id)
                                - `logger.debug()` for detailed reasoning (full plan contents, LLM response details, subreddit selection logic)
                                - `logger.warning()` for adjustments (truncating subreddit list, fallback behavior)
                                - `logger.error()` for failures (validation errors, LLM call failures)
                                - Never use `print()` statements
- Validate output matches Pydantic schema before returning
- Optional: cache or log plans for later reuse (implementation detail left to consumer)

---

## LLM Prompt Template

**System Prompt:**

```
You are a search planning assistant for a DIY project Q&A system.

Given a user query, generate a structured search plan containing:
1. search_terms: List of 2-5 specific keywords or phrases to search Reddit
2. subreddits: Choose 1-3 relevant subreddits from {diy, homeimprovement, woodworking} based on query intent
3. notes: Brief explanation of your reasoning (1-2 sentences)

Subreddit Selection Guidelines:
- For general or ambiguous queries (e.g., "fix door hinge"), default to including "diy"
- For specific queries, choose the most relevant subreddit(s):
  - "homeimprovement" for house/property/renovation questions
  - "woodworking" for furniture/carpentry/woodcraft questions
  - You may omit "diy" if the query is clearly specialized
- Maximum 3 subreddits; prioritize relevance over breadth

Search Term Guidelines:
- Use specific, actionable phrases (e.g., "deck waterproofing", "cabinet hinge repair")
- Keep search_terms focused and relevant
- Avoid overly broad terms like "help" or "advice" alone

Output must be valid JSON matching this schema:
{
  "search_terms": ["term1", "term2", ...],
  "subreddits": ["diy", ...],
  "notes": "reasoning here"
}
```

**User Message:**

```
User query: {user_query}
```

**Example I/O:**

*Input:* "How do I refinish a dining table?"

*Output:*

```json
{
  "search_terms": ["refinish table", "wood refinishing", "table restoration"],
  "subreddits": ["woodworking", "diy"],
  "notes": "Table refinishing is primarily a woodworking task, with r/woodworking being the primary resource. r/diy also covers general furniture projects."
}
```

*Input:* "Installing drywall in basement"

*Output:*

```json
{
  "search_terms": ["basement drywall install", "drywall installation", "finishing drywall"],
  "subreddits": ["homeimprovement"],
  "notes": "Drywall installation is a home improvement task best covered in r/homeimprovement. Omitting r/diy since this is clearly a specialized renovation query."
}
```

---

## Integration Points

**Reuse existing code:**

- `services/ingestion/openai_client.py::get_openai_client()` → OpenAI client
- `config/logging_config.py` → logging setup (already configured)

**Conceptual relationship to RAG filter logic:**

- Existing RAG filters (`TITLE_PATTERNS`, `include_post()` in `services/ingestion/content_filters.py`) were designed for hard-filtering posts
- In the agentic architecture, these patterns inform **relevance guidance** rather than hard exclusion
- The LLM reasoning layer (not the planner, but downstream agent components) determines final usefulness
- Planner generates search terms inspired by similar quality heuristics but delegates final filtering to the agent

**Output consumed by:**

- `services/ingestion/fetch_data.py` → expects subreddit names and search queries
- Existing filters in `services/ingestion/content_filters.py` → may be reused for soft relevance scoring
- Batching and rate limiting are handled by the fetcher, not the planner

**Conversion layer (future):**

The consumer will need to:

1. Join `search_terms` list into Reddit query format: `" OR ".join(search_terms)`
2. Call `fetch_posts()` for each subreddit in `subreddits` list
3. Pass `plan_id` through the pipeline for traceability

**Caching and logging:**

- Planner outputs may be cached or logged for later reuse (design detail left to consumer)
- `plan_id` enables correlation across logs (planner → fetcher → filters → agent)

---

## Developer Validation

### Smoke Test Script

**Script file:** `scripts/planner_smoke_test.py`

**Purpose:** Manual validation script for developers to test Planner logic with real LLM calls. Lives in `scripts/` alongside other developer utilities (data refresh tools, manual validation scripts, etc.) - not part of automated test suite.

**Features:**

- Runs real planner logic (no mocks or stubs)
- Accepts optional CLI arguments for custom queries
- Uses existing `config/logging_config` setup (no print statements)
- INFO-level logs summarize progress and results (including plan_id)
- DEBUG-level logs show full plan details
- Simple, plug-and-play design

**Usage:**

```bash
# Run with default test queries
python -m scripts.planner_smoke_test

# Run with custom queries
python -m scripts.planner_smoke_test "fix sticky drawer" "refinish table" "install deck railing"
```

**Implementation outline:**

```python
import sys
from config.logging_config import configure_logging, get_logger
from agent.planner import create_search_plan

configure_logging()
logger = get_logger(__name__)

def main():
    # Default queries if none provided
    queries = sys.argv[1:] if len(sys.argv) > 1 else [
        "How do I refinish hardwood floors?",
        "Best way to repair drywall holes",
        "Building a deck - what wood should I use?",
        "Fix sticky drawer",
    ]
    
    logger.info(f"Running planner smoke test with {len(queries)} queries")
    
    for query in queries:
        logger.info(f"Testing query: {query}")
        try:
            plan = create_search_plan(query)
            logger.info(f"Plan generated successfully [plan_id={plan.plan_id}]")
            logger.debug(f"Search terms: {plan.search_terms}")
            logger.debug(f"Subreddits: {plan.subreddits}")
            logger.debug(f"Notes: {plan.notes}")
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
    
    logger.info("Smoke test complete")

if __name__ == "__main__":
    main()
```

**Validation:**

- Script executes without errors
- Each query produces a valid `SearchPlan` with unique `plan_id`
- Logs are structured and informative
- Output respects subreddit selection rules (1-3 from valid set)
- Subreddit selection shows dynamic behavior (not always including "diy")

---

## Dependencies

**Add to `requirements.txt`:**

```
pydantic>=2.0.0
```

(OpenAI client already present)

---

## Success Criteria

1. ✅ Proper subpackage structure: `agent/planner/__init__.py` and `agent/planner/core.py`
2. ✅ Pydantic models in `agent/models.py` (~30-40 lines with plan_id)
3. ✅ Follows project conventions (type hints, logging, DRY, KISS)
4. ✅ No global imports - explicit Pythonic import style
5. ✅ Smoke test runner at `tests/runner_planner.py` (~40-50 lines)
6. ✅ Does not modify any `services/ingestion` or `config` code
7. ✅ Production-grade error handling and validation
8. ✅ Proper logging levels (info/debug/warning/error, no prints)
9. ✅ Dynamic subreddit selection based on query intent
10. ✅ plan_id for traceability across pipeline
11. ✅ Clear separation: planner generates plans, fetcher handles batching/rate limiting