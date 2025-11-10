"""End-to-end evaluation helper: generate plans and fetch Reddit results."""

from __future__ import annotations

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List

import typer

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from agent.planner.core import create_search_plan
from config.logging_config import get_logger
from services.fetch.reddit_fetcher import run_reddit_fetcher

logger = get_logger(__name__)
app = typer.Typer(add_completion=False)

DEFAULT_QUERIES: List[str] = [
    "how to caulk bathtub",
    "how to repair holes in drywall",
    "how to mount a TV safely",
    "how to hang floating wall shelves",
    "how to build a raised garden bed"
    #"how to install vinyl flooring", 
    #"how to fix chipped wall paint",
    #"how to fix a broken light fixture or loose outlet cover",
    #"how to paint a room properly",
    #"how to hang picture frames straight",
]

EVAL_DIR = Path("data/eval_runs")


def _load_queries(queries_file: Path | None) -> list[str]:
    if queries_file is None:
        return DEFAULT_QUERIES

    contents = queries_file.read_text(encoding="utf-8")
    queries = [line.strip() for line in contents.splitlines() if line.strip()]
    if not queries:
        raise typer.BadParameter(f"No queries found in {queries_file}")
    return queries


@app.command()
def run(
    queries_file: Path | None = typer.Option(
        None, "--queries-file", help="Optional file with one query per line."
    ),
    post_limit: int = typer.Option(10, "--post-limit", help="Posts per (subreddit, term)."),
    environment: str = typer.Option("dev", "--environment", help="Reddit client environment."),
) -> None:
    """Generate SearchPlans and FetchResults for a list of queries."""
    queries = _load_queries(queries_file)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Running fetch evaluation for %d queries (post_limit=%d)", len(queries), post_limit)

    summary: list[dict] = []

    for query in queries:
        logger.info("Processing query: %s", query)
        try:
            plan = create_search_plan(query)
        except Exception as exc:
            logger.error("Planner failed for query '%s': %s", query, exc)
            summary.append(
                {
                    "query": query,
                    "status": "planner_failed",
                    "error": str(exc),
                }
            )
            continue

        try:
            fetch_result = run_reddit_fetcher(
                plan=plan,
                post_limit=post_limit,
                environment=environment,
            )
        except Exception as exc:
            logger.error("Fetcher failed for query '%s': %s", query, exc)
            summary.append(
                {
                    "query": query,
                    "plan_id": str(plan.plan_id),
                    "status": "fetch_failed",
                    "error": str(exc),
                }
            )
            continue

        accepted_posts = len(fetch_result.posts)
        accepted_comments = sum(len(post.comments) for post in fetch_result.posts)

        logger.info("Accepted %d posts for query '%s'", accepted_posts, query)

        summary.append(
            {
                "query": query,
                "plan_id": str(plan.plan_id),
                "search_terms": plan.search_terms,
                "subreddits": plan.subreddits,
                "accepted_posts": accepted_posts,
                "accepted_comments": accepted_comments,
                "status": "ok",
            }
        )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    summary_path = EVAL_DIR / f"fetch_eval_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Fetch evaluation complete (summary saved to %s).", summary_path)


if __name__ == "__main__":
    app()
