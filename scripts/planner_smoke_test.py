import typer
from config.logging_config import get_logger
from agent.planner import create_search_plan

DEFAULT_QUERIES = [
    "How do I sand the finish off this dresser?",
    "How to caulk around bathroom sink fixtures?",
    "How can I install this projector on ceiling",
]

logger = get_logger(__name__)
app = typer.Typer(add_completion=False)


@app.command()
def run(queries: list[str] = typer.Argument(None, help="Queries to generate plans for")) -> None:
    """Planner smoke test; generates SearchPlans for provided queries."""
    active_queries = queries or DEFAULT_QUERIES
    logger.info("Running planner smoke test with %d queries", len(active_queries))

    for query in active_queries:
        logger.info("Testing query: %s", query)
        try:
            plan = create_search_plan(query)
            logger.info("Query: %s", plan.query)
            logger.debug("Search terms: %s", plan.search_terms)
            logger.debug("Subreddits: %s", plan.subreddits)
            logger.debug("Notes: %s", plan.notes)
        except Exception as exc:
            logger.error("Failed to generate plan for query %s: %s", query, exc)

    logger.info("Smoke test complete")


if __name__ == "__main__":
    app()
