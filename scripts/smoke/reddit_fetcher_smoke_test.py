"""Smoke test for the Reddit fetcher pipeline."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import typer

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from agent.planner.model import SearchPlan
from services.fetch.reddit_fetcher import run_reddit_fetcher
from config.logging_config import get_logger

app = typer.Typer(add_completion=False)
logger = get_logger(__name__)


@app.command()
def run(
    plan_path: Path = typer.Argument(..., help="Path to a serialized SearchPlan JSON file."),
    post_limit: int = typer.Option(10, "--post-limit", help="Posts per (subreddit, term)."),
    environment: str = typer.Option("dev", "--environment", help="Reddit client environment."),
    save_json: bool = typer.Option(False, "--save-json/--no-save-json", help="Persist FetchResult under data/fetch_results/."),
) -> None:
    """Execute the Reddit fetcher against a stored SearchPlan."""
    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    plan = SearchPlan.model_validate(plan_data)

    plan_query = getattr(plan, "query", "")
    logger.info("Executing fetcher smoke test")
    logger.info("  query: %s", plan_query)
    logger.info("  post_limit: %d", post_limit)
    logger.info("  plan_id: %s", plan.plan_id)

    fetch_result = run_reddit_fetcher(
        plan=plan,
        post_limit=post_limit,
        environment=environment,
    )

    total_possible = len(plan.subreddits) * len(plan.search_terms) * post_limit
    accepted_count = len(fetch_result.posts)
    percent = (accepted_count / total_possible * 100) if total_possible else 0
    logger.info(
        "Fetch completed: %d/%d posts accepted (%.1f%%).",
        accepted_count,
        total_possible,
        percent,
    )
    _log_accepted_posts(fetch_result)

    if save_json:
        output_dir = Path("data/fetch_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        short_id = getattr(plan.plan_id, "hex", None)
        short_id = short_id[:8] if short_id else plan.plan_id
        output_path = output_dir / f"fetch_result_{short_id}.json"
        output_path.write_text(fetch_result.model_dump_json(indent=2), encoding="utf-8")
        logger.info("FetchResult JSON saved to %s", output_path)


def _log_accepted_posts(fetch_result) -> None:
    posts = fetch_result.posts
    if not posts:
        logger.info("No posts accepted.")
        return

    max_preview = min(5, len(posts))
    logger.info("Accepted posts (showing %d of %d):", max_preview, len(posts))
    for post in posts[:max_preview]:
        subreddit = post.subreddit
        logger.info(
            "  - %s — %s (comments=%d, karma=%d) %s",
            subreddit,
            post.title,
            len(post.comments),
            post.post_karma,
            post.url,
        )

if __name__ == "__main__":
    app()
