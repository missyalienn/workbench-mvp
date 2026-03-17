import logging
from pathlib import Path
import sys

import typer

# Ensure repo root is on sys.path when running directly
if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import get_logger, configure_logging
from agent.planner import create_search_plan

DEFAULT_QUERIES = [
    "how to caulk bathtub",
    "how to repair holes in drywall",
    "how to install peel and stick vinyl flooring in an apartment",
    "how to touch up chipped wall paint",
    "how to mount a TV safely",
    "how to hang picture frames straight",
    "how to hang floating wall shelves",
    "how to build a raised garden bed",
    "how to fix a broken light fixture or loose outlet cover",
    "how to paint a room properly",
]

logger = get_logger(__name__)
app = typer.Typer(add_completion=False)


@app.command()
def run(
    queries: list[str] = typer.Argument(None, help="Queries to generate plans for"),
    debug: bool = typer.Option(False, "--debug/--no-debug", help="Enable verbose logging"),
) -> None:
    """Planner smoke test; generates SearchPlans for provided queries."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    active_queries = queries or DEFAULT_QUERIES
    logger.info("Running planner smoke test with %d queries", len(active_queries))

    for query in active_queries:
        try:
            plan = create_search_plan(query)
            logger.info(
                'Plan OK [plan_id=%s] query="%s" terms=%s subs=%s notes="%s"',
                plan.plan_id,
                plan.query,
                plan.search_terms,
                plan.subreddits,
                plan.notes,
            )
        except Exception as exc:
            logger.error("Planner failed for query %s: %s", query, exc, exc_info=debug)

    logger.info("Smoke test complete")


if __name__ == "__main__":
    app()
