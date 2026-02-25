"""
Manual scoring harness aligned with RedditFetcher keyword scoring.

Runs Reddit search using the same transport defaults as the fetcher, applies the
fetcher validation gate (`passes_post_validation`), then evaluates keyword
relevance to report how many posts pass the threshold. Logs summary counts per
(subreddit, search term) pair and across all pairs.

Run:
    python3 scripts/manual_score_test.py --subreddit diy --search-term "leaky faucet fix" --limit 15
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from agent.planner.core import create_search_plan
from config.logging_config import configure_logging, get_logger
from services.reddit_client import RedditClient
from services.fetch.reddit_validation import passes_post_validation
from services.fetch.scoring import evaluate_post_relevance
from services.fetch.utils.text_utils import clean_text

DEFAULT_QUERIES = [
    "how to caulk bathtub",
    "how to repair holes in drywall",
    "how to mount a TV safely",
]
logger = get_logger(__name__)


def main() -> None:
    args = parse_args()
    configure_logging()
    logging.getLogger("services.fetch.scoring").setLevel(logging.INFO)

    log_path = attach_file_logger()
    logger.info(
        "Manual scoring run | queries=%s | limit=%d | pause=%.1fs",
        args.queries,
        args.limit,
        args.pause,
    )
    logger.info("Log file: %s", log_path)

    client = RedditClient()
    total_fetched = 0
    total_considered = 0
    total_passed = 0
    pair_summaries: list[str] = []

    for query in args.queries:
        logger.info('Query: "%s"', query)
        plan = create_search_plan(query)
        logger.info(
            "Plan: subreddits=%s | search_terms=%s",
            plan.subreddits,
            plan.search_terms,
        )
        for subreddit in plan.subreddits:
            for term in plan.search_terms:
                pair_fetched = 0
                pair_considered = 0
                pair_passed = 0
                logger.info(
                    "Fetching posts for r/%s | search_term='%s'",
                    subreddit,
                    term,
                )
                for post in client.paginate_search(
                    subreddit=subreddit,
                    query=term,
                    limit=args.limit,
                ):
                    post_id = post.get("id")
                    if not post_id:
                        continue
                    pair_fetched += 1
                    total_fetched += 1
                    if not passes_post_validation(post):
                        continue
                    pair_considered += 1
                    total_considered += 1
                    post_karma = post.get("score", 0)
                    title = clean_text(post.get("title", ""))
                    body = clean_text(post.get("selftext", ""))
                    relevance, positives, negatives, passed = evaluate_post_relevance(
                        post_id=post_id,
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
                        pair_passed += 1
                        total_passed += 1

                sleep(args.pause)
                pair_summaries.append(
                    "Summary (pair): passed "
                    f"{pair_passed}/{pair_considered} posts for r/{subreddit} "
                    f"| search_term='{term}' | query='{query}'"
                )

    for summary in pair_summaries:
        logger.info(summary)
    logger.info("Summary (all): passed %d/%d posts", total_passed, total_considered)
    logger.info(
        "Summary (all): considered %d/%d fetched posts",
        total_considered,
        total_fetched,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Reddit posts and run keyword relevance scoring.",
    )
    parser.add_argument(
        "--query",
        dest="queries",
        action="append",
        default=None,
        help="Query to generate a planner SearchPlan (repeat for multiple).",
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
    args.queries = args.queries or DEFAULT_QUERIES
    return args


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
