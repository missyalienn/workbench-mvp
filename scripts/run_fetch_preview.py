"""Generate a preview JSON of fetch results for manual inspection."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, UTC
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
    "how to install laminate flooring in an apartment",
    "how to touch up chipped wall paint",
    "how to mount a TV safely",
    "how to remove scratches from wood table",
    "how to hang floating wall shelves",
    "how to build a raised garden bed",
    "how to fix a broken light fixture",
    "how to paint a room properly",
]

PREVIEW_DIR = Path("data/fetch_previews")


def _load_queries(queries_file: Path | None) -> list[str]:
    if queries_file is None:
        return DEFAULT_QUERIES

    contents = queries_file.read_text(encoding="utf-8")
    queries = [line.strip() for line in contents.splitlines() if line.strip()]
    if not queries:
        raise typer.BadParameter(f"No queries found in {queries_file}")
    return queries


def _post_preview(post, max_comments: int = 5) -> dict:
    comments_preview = [
        {
            "comment_id": comment.comment_id,
            "body": comment.body,
            "comment_karma": comment.comment_karma,
        }
        for comment in post.comments[:max_comments]
    ]
    return {
        "title": post.title,
        "subreddit": _infer_subreddit(post.url),
        "permalink": post.url,
        "post_karma": post.post_karma,
        "relevance_score": post.relevance_score,
        "matched_keywords": post.matched_keywords,
        "comment_count": len(post.comments),
        "comments": comments_preview,
    }


def _infer_subreddit(url: str) -> str:
    marker = "/r/"
    if marker in url:
        start = url.index(marker) + len(marker)
        end = url.find("/", start)
        if end == -1:
            end = len(url)
        name = url[start:end]
        if name:
            return f"r/{name}"
    return "r/?"


@app.command()
def run(
    queries_file: Path | None = typer.Option(
        None, "--queries-file", help="Optional file with one query per line."
    ),
    post_limit: int = typer.Option(10, "--post-limit", help="Posts per (subreddit, term)."),
    environment: str = typer.Option("dev", "--environment", help="Reddit client environment."),
    max_posts: int = typer.Option(5, "--max-posts", help="Preview up to N posts per query."),
    max_comments: int = typer.Option(5, "--max-comments", help="Preview up to N comments per post."),
) -> None:
    """Produce a JSON file with real post/comment content for inspection."""
    queries = _load_queries(queries_file)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Running fetch preview for %d queries", len(queries))
    preview_payload: list[dict] = []

    for query in queries:
        logger.info("Processing query: %s", query)
        try:
            plan = create_search_plan(query)
        except Exception as exc:
            logger.error("Planner failed for query '%s': %s", query, exc)
            preview_payload.append(
                {
                    "query": query,
                    "status": "planner_failed",
                    "error": str(exc),
                }
            )
            continue

        try:
            start = time.perf_counter()
            fetch_result = run_reddit_fetcher(
                plan=plan,
                post_limit=post_limit,
                environment=environment,
            )
            elapsed = time.perf_counter() - start
            logger.info(
                "Fetch done in %.2fs (subreddits=%d, terms=%d)",
                elapsed,
                len(plan.subreddits),
                len(plan.search_terms),
            )
        except Exception as exc:
            logger.error("Fetcher failed for query '%s': %s", query, exc)
            preview_payload.append(
                {
                    "query": query,
                    "plan_id": str(plan.plan_id),
                    "search_terms": plan.search_terms,
                    "subreddits": plan.subreddits,
                    "status": "fetch_failed",
                    "error": str(exc),
                }
            )
            continue

        posts_preview = [
            _post_preview(post, max_comments=max_comments) for post in fetch_result.posts[:max_posts]
        ]

        preview_payload.append(
            {
                "query": query,
                "plan_id": str(plan.plan_id),
                "search_terms": plan.search_terms,
                "subreddits": plan.subreddits,
                "accepted_posts": len(fetch_result.posts),
                "posts_preview": posts_preview,
                "status": "ok",
            }
        )

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    preview_path = PREVIEW_DIR / f"fetch_preview_{timestamp}.json"
    preview_path.write_text(json.dumps(preview_payload, indent=2), encoding="utf-8")
    logger.info("Fetch preview saved to %s", preview_path)


if __name__ == "__main__":
    app()
