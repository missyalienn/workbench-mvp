from concurrent.futures import ThreadPoolExecutor, as_completed

from agent.planner.model import SearchPlan
from config.logging_config import get_logger
from config.settings import settings
from services.http.retry_policy import RateLimitError, RetryableFetchError
from services.reddit_client import RedditClient

from .comment_pipeline import filter_comments
from .content_filters import has_seen_post, is_post_too_short
from .reddit_builders import build_comment_models, build_post_model
from .reddit_validation import passes_post_validation
from .schemas import FetchResult, Post
from .scoring import evaluate_post_relevance
from .utils.datetime_utils import utc_now
from .utils.text_utils import clean_text

logger = get_logger(__name__)


def _fetch_posts_for_pair(
    *,
    subreddit: str,
    term: str,
    post_limit: int,
    fetched_at: float,
    client: RedditClient | None = None,
) -> list[Post]:
    """Fetch and filter posts for a single (subreddit, term) pair."""
    accepted: list[Post] = []
    local_seen_post_ids: set[str] = set()
    reddit_client = client or RedditClient()

    try:
        for raw_post in reddit_client.paginate_search(
            subreddit=subreddit,
            query=term,
            limit=post_limit,
        ):
            post_id = raw_post.get("id")
            if not post_id:
                logger.info(
                    "Rejecting post without ID (subreddit=%s, term=%s)",
                    subreddit,
                    term,
                )
                continue

            if not passes_post_validation(raw_post):
                continue

            title = clean_text(raw_post.get("title", ""))
            body = clean_text(raw_post.get("selftext", ""))

            score, positives, _, passed = evaluate_post_relevance(
                post_id=post_id,
                title=title,
                body=body,
            )
            if not passed:
                logger.info("Rejecting post %s: below_threshold", post_id)
                continue

            if is_post_too_short(body):
                logger.info("Rejecting post %s: too_short", post_id)
                continue

            if has_seen_post(post_id, local_seen_post_ids):
                logger.info("Rejecting post %s: duplicate", post_id)
                continue

            try:
                raw_comments = reddit_client.fetch_comments(post_id=post_id)
            except RateLimitError as exc:
                logger.warning(
                    "429: Too many requests while fetching comments (post_id=%s): %s",
                    post_id,
                    exc,
                )
                continue
            except RetryableFetchError as exc:
                logger.warning(
                    "Comments fetch failed after retries (post_id=%s): %s",
                    post_id,
                    exc,
                )
                continue

            filtered_comments = filter_comments(
                post_id=post_id,
                raw_comments=raw_comments,
            )

            comment_models = build_comment_models(filtered_comments, fetched_at)
            if not comment_models:
                logger.info("Rejecting post %s: no_comments", post_id)
                continue

            post_model = build_post_model(
                raw_post=raw_post,
                cleaned_title=title,
                cleaned_body=body,
                relevance_score=score,
                matched_keywords=positives,
                comments=comment_models,
                fetched_at=fetched_at,
            )
            accepted.append(post_model)
    except RateLimitError as exc:
        logger.warning(
            "429: Too many requests while searching (subreddit=%s, term=%s): %s",
            subreddit,
            term,
            exc,
        )
    except RetryableFetchError as exc:
        logger.warning(
            "Search failed after retries (subreddit=%s, term=%s): %s",
            subreddit,
            term,
            exc,
        )
    return accepted


def run_reddit_fetcher(
    plan: SearchPlan,
    *,
    post_limit: int,
    environment: str = "dev",
) -> FetchResult:
    """
    Orchestrate the Reddit fetch pipeline for a planner-produced SearchPlan.
    """
    fetched_at = utc_now()
    accepted_posts: list[Post] = []
    seen_post_ids: set[str] = set()
    plan_query = plan.query

    tasks = [
        (subreddit, term)
        for subreddit in plan.subreddits
        for term in plan.search_terms
    ]

    def _merge_posts(posts: list[Post]) -> None:
        for post in posts:
            post_id = getattr(post, "id", None)
            if not post_id or post_id in seen_post_ids:
                continue
            seen_post_ids.add(post_id)
            accepted_posts.append(post)

    if not settings.FETCHER_ENABLE_CONCURRENCY:
        client = RedditClient()
        for subreddit, term in tasks:
            posts = _fetch_posts_for_pair(
                client=client,
                subreddit=subreddit,
                term=term,
                post_limit=post_limit,
                fetched_at=fetched_at,
            )
            _merge_posts(posts)
    else:
        max_workers = max(1, settings.FETCHER_MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    _fetch_posts_for_pair,
                    subreddit=subreddit,
                    term=term,
                    post_limit=post_limit,
                    fetched_at=fetched_at,
                ): (subreddit, term)
                for subreddit, term in tasks
            }
            for future in as_completed(future_map):
                subreddit, term = future_map[future]
                try:
                    posts = future.result()
                except Exception as exc:
                    logger.warning(
                        "Concurrent fetch failed (subreddit=%s, term=%s): %s",
                        subreddit,
                        term,
                        exc,
                    )
                    continue
                _merge_posts(posts)

    return FetchResult(
        query=plan_query,
        plan_id=plan.plan_id,
        search_terms=plan.search_terms,
        subreddits=plan.subreddits,
        fetched_at=fetched_at,
        source="reddit",
        posts=accepted_posts,
    )


__all__ = ["run_reddit_fetcher"]
