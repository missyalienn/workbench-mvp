"""Manual scoring harness for RedditFetcher keyword weights."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Any

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import configure_logging, get_logger
from services.reddit_client import RedditClient
from services.fetch.scoring import evaluate_post_relevance
from services.fetch.text_utils import clean_text

DEFAULT_SUBREDDITS = ["diy"]
DEFAULT_TERMS = ["leaky faucet fix"]
SHOWCASE_SCORE_THRESHOLD = 2000

logger = get_logger(__name__)
API_BASE_URL = "https://oauth.reddit.com"


def main() -> None:
    args = parse_args()
    configure_logging()
    logging.getLogger("services.fetch.scoring").setLevel(logging.INFO)

    log_path = attach_file_logger()
    logger.info(
        "Manual scoring run | subreddits=%s | search_terms=%s | limit=%d | pause=%.1fs",
        args.subreddits,
        args.search_terms,
        args.limit,
        args.pause,
    )
    logger.info("Log file: %s", log_path)

    client = RedditClient()
    session = client.session()

    total = 0
    accepted = 0

    for subreddit in args.subreddits:
        for term in args.search_terms:
            logger.info("Fetching posts for r/%s | search_term='%s'", subreddit, term)
            posts = fetch_posts(session, subreddit, term, args.limit)
            if not posts:
                logger.warning(
                    "No posts returned for r/%s | search_term='%s'", subreddit, term
                )
                continue

            for post in posts:
                total += 1
                post_karma = post.get("score", 0)
                if post_karma is not None and post_karma > SHOWCASE_SCORE_THRESHOLD:
                    logger.info(
                        "[REJECTED] r/%s | post_karma=%s | reason=high_score_threshold | title='%s'",
                        subreddit,
                        post_karma,
                        post.get("title", "")[:80],
                    )
                    continue
                title = clean_text(post.get("title", ""))
                body = clean_text(post.get("selftext", ""))
                relevance, positives, negatives, passed = evaluate_post_relevance(
                    post_id=post.get("id", "unknown"),
                    title=title,
                    body=body,
                )

                snippet = title[:80]
                logger.info(
                    "[%s] r/%s | post_karma=%s | relevance=%.2f | title='%s' | positives=%s | negatives=%s",
                    "ACCEPTED" if passed else "REJECTED",
                    subreddit,
                    post_karma,
                    relevance,
                    snippet,
                    positives,
                    negatives,
                )

                if passed:
                    accepted += 1

            sleep(args.pause)

    logger.info("Summary: accepted %d/%d posts", accepted, total)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Reddit posts and run keyword relevance scoring.",
    )
    parser.add_argument(
        "--subreddit",
        dest="subreddits",
        action="append",
        default=None,
        help="Subreddit to query (repeat for multiple). Default: diy",
    )
    parser.add_argument(
        "--search-term",
        dest="search_terms",
        action="append",
        default=None,
        help="Search term (repeat for multiple). Default: 'leaky faucet fix'",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Maximum posts per subreddit/term combination. Default: 15",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=1.0,
        help="Seconds to pause between subreddit queries. Default: 1.0",
    )
    args = parser.parse_args()
    args.subreddits = args.subreddits or DEFAULT_SUBREDDITS
    args.search_terms = args.search_terms or DEFAULT_TERMS
    return args


def fetch_posts(
    session: Any, subreddit: str, term: str, limit: int
) -> list[dict[str, Any]]:
    params = {
        "q": term,
        "limit": limit,
        "sort": "relevance",
        "restrict_sr": 1,
        "include_over_18": 1,
    }
    response = session.get(
        f"{API_BASE_URL}/r/{subreddit}/search",
        params=params,
        timeout=10,
    )
    try:
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - manual script
        logger.error(
            "Reddit request failed | r/%s | search_term='%s' | status=%s | error=%s",
            subreddit,
            term,
            response.status_code,
            exc,
        )
        return []

    data = response.json()
    children = data.get("data", {}).get("children", [])
    return [child.get("data", {}) for child in children if child.get("data")]


def attach_file_logger() -> Path:
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%m-%d_%H-%M-%S")
    log_path = logs_dir / f"manual_score_test_{timestamp}.log"

    root_logger = logging.getLogger()
    formatter = root_logger.handlers[0].formatter if root_logger.handlers else None
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    if formatter:
        file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    return log_path


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:  # pragma: no cover - manual script
        logger.warning("Manual scoring interrupted by user.")
