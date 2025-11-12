from typing import Any

from agent.planner.model import SearchPlan
from services.reddit_client import RedditClient
from .reddit_validation import passes_post_validation
from .content_filters import (
    is_post_too_short,
    has_seen_post,
)
from .comment_pipeline import filter_comments
from .utils.text_utils import clean_text
from .utils.datetime_utils import utc_now
from .scoring import evaluate_post_relevance
from .schemas import Post, Comment, FetchResult
from .reddit_builders import (
    build_comment_models,
    build_post_model,
)
from config.logging_config import get_logger

logger = get_logger(__name__)

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
    seen_post_ids: set[str] = set()
    accepted_posts: list[Post] = []
    plan_query = plan.query
    client = RedditClient()

    for subreddit in plan.subreddits:
        for term in plan.search_terms:
            for raw_post in client.paginate_search(
                subreddit=subreddit,
                query=term,
                limit=post_limit,
            ):
                post_id = raw_post.get("id")
                if not post_id:
                    logger.info("Rejecting post without ID (subreddit=%s, term=%s)", subreddit, term)
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

                if has_seen_post(post_id, seen_post_ids):
                    logger.info("Rejecting post %s: duplicate", post_id)
                    continue

                raw_comments = client.fetch_comments(post_id=post_id)
                filtered_comments = filter_comments(post_id=post_id, raw_comments=raw_comments)

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
                accepted_posts.append(post_model)

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