import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import copy_context
from dataclasses import dataclass
from typing import Any

from agent.clients.openai_client import get_openai_client
from agent.planner.model import SearchPlan
from common.exceptions import ExternalTimeoutError, RateLimitError, InvalidResponseError
from config.logging_config import get_logger
from config.settings import settings
from services.embedding.client import EmbeddingClient, EmbeddingError
from services.embedding.ranking import RankingInput, embed_query, rank_candidates, zero_score_posts
from services.embedding.store_factory import get_vector_store
from services.reddit_client import RedditClient

from .comment_pipeline import filter_comments
from .content_filters import has_seen_post, is_post_too_short
from .reddit_builders import build_comment_models, build_post_model
from .reddit_validation import passes_post_validation
from .schemas import Comment, FetchResult, Post
from .scoring import evaluate_post_relevance
from .utils.datetime_utils import utc_now
from .utils.text_utils import clean_text

logger = get_logger(__name__)


@dataclass(frozen=True)
class PostCandidate:
    """Post data assembled before scoring."""

    raw_post: dict[str, Any]
    cleaned_title: str
    cleaned_body: str
    comments: list[Comment]
    fetched_at: float


def _score_post_candidates(candidates: list[PostCandidate]) -> list[Post]:
    scored: list[Post] = []
    for candidate in candidates:
        post_id = candidate.raw_post.get("id", "")
        score, positives, _, passed = evaluate_post_relevance(
            post_id=post_id,
            title=candidate.cleaned_title,
            body=candidate.cleaned_body,
        )
        if not passed:
            logger.info("fetch.post_rejected", reason="below_threshold", post_id=post_id)
            continue

        post_model = build_post_model(
            raw_post=candidate.raw_post,
            cleaned_title=candidate.cleaned_title,
            cleaned_body=candidate.cleaned_body,
            relevance_score=score,
            matched_keywords=positives,
            comments=candidate.comments,
            fetched_at=candidate.fetched_at,
        )
        scored.append(post_model)
    return scored


def _fetch_posts_for_pair(
    *,
    subreddit: str,
    term: str,
    post_limit: int,
    fetched_at: float,
    client: RedditClient | None = None,
) -> list[PostCandidate]:
    """Fetch and filter posts for a single (subreddit, term) pair."""
    candidates: list[PostCandidate] = []
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
                logger.info("fetch.post_rejected", reason="no_id", subreddit=subreddit, term=term)
                continue

            if not passes_post_validation(raw_post):
                continue

            title = clean_text(raw_post.get("title", ""))
            body = clean_text(raw_post.get("selftext", ""))

            if is_post_too_short(body):
                logger.info("fetch.post_rejected", reason="too_short", post_id=post_id)
                continue

            if has_seen_post(post_id, local_seen_post_ids):
                logger.info("fetch.post_rejected", reason="duplicate", post_id=post_id)
                continue

            try:
                raw_comments = reddit_client.fetch_comments(post_id=post_id)
            except (ExternalTimeoutError, RateLimitError, InvalidResponseError) as exc:
                logger.warning("fetch.request_failed", context="comments", post_id=post_id, exc_type=type(exc).__name__, error=str(exc))
                continue

            filtered_comments = filter_comments(
                post_id=post_id,
                raw_comments=raw_comments,
                max_comments=settings.FETCHER_MAX_COMMENTS_PER_POST,
            )

            comment_models = build_comment_models(filtered_comments, fetched_at)
            if not comment_models:
                logger.info("fetch.post_rejected", reason="no_comments", post_id=post_id)
                continue

            candidates.append(
                PostCandidate(
                    raw_post=raw_post,
                    cleaned_title=title,
                    cleaned_body=body,
                    comments=comment_models,
                    fetched_at=fetched_at,
                )
            )
    except (ExternalTimeoutError, RateLimitError, InvalidResponseError) as exc:
        logger.warning("fetch.request_failed", context="search", subreddit=subreddit, term=term, exc_type=type(exc).__name__, error=str(exc))
    return candidates


def _context_wrapper(fn, /, **kwargs):
    """Run fn(**kwargs) inside a copy of the current contextvars context.

    Captures the calling thread's context at dispatch time so that
    structlog's bound variables (e.g. plan_id) are visible inside worker threads.
    """
    ctx = copy_context()
    return ctx.run(fn, **kwargs)


def run_reddit_fetcher(
    plan: SearchPlan,
    *,
    post_limit: int,
    environment: str = "dev",
) -> FetchResult:
    """
    Orchestrate the Reddit fetch pipeline for a planner-produced SearchPlan.
    """
    t0 = time.monotonic()
    fetched_at = utc_now()
    accepted_posts: list[Post] = []
    candidate_posts: list[PostCandidate] = []
    seen_post_ids: set[str] = set()
    plan_query = plan.query

    tasks = [
        (subreddit, term)
        for subreddit in plan.subreddits
        for term in plan.search_terms
    ]
    logger.info("fetch.start", n_tasks=len(tasks), post_limit=post_limit)

    def _merge_candidates(candidates: list[PostCandidate]) -> None:
        for candidate in candidates:
            post_id = candidate.raw_post.get("id")
            if not post_id or post_id in seen_post_ids:
                continue
            seen_post_ids.add(post_id)
            candidate_posts.append(candidate)

    if not settings.FETCHER_ENABLE_CONCURRENCY:
        client = RedditClient()
        for subreddit, term in tasks:
            candidates = _fetch_posts_for_pair(
                client=client,
                subreddit=subreddit,
                term=term,
                post_limit=post_limit,
                fetched_at=fetched_at,
            )
            _merge_candidates(candidates)
    else:
        max_workers = max(1, settings.FETCHER_MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    _context_wrapper,
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
                    candidates = future.result()
                except Exception as exc:
                    logger.warning("fetch.concurrent_failed", subreddit=subreddit, term=term, error=str(exc))
                    continue
                _merge_candidates(candidates)

    if settings.USE_SEMANTIC_RANKING:
        try:
            client = get_openai_client()
            store = get_vector_store()
            embedder = EmbeddingClient(
                client=client,
                model=settings.EMBEDDING_MODEL,
                store=store,
            )
            ranking_input = RankingInput(query=plan_query, candidates=candidate_posts)
            query_embedding = embed_query(ranking_input, embedder)
            accepted_posts = rank_candidates(ranking_input, query_embedding, embedder)
            logger.info("fetch.complete", elapsed_ms=int((time.monotonic() - t0) * 1000), n_candidates=len(candidate_posts), n_ranked=len(accepted_posts))
        except EmbeddingError as exc:
            logger.warning("fetch.ranking_fallback", error=str(exc))
            accepted_posts = zero_score_posts(candidate_posts)
            logger.info("fetch.complete", elapsed_ms=int((time.monotonic() - t0) * 1000), n_candidates=len(candidate_posts), n_ranked=len(accepted_posts))
    else:
        accepted_posts = _score_post_candidates(candidate_posts)
        logger.info("fetch.complete", elapsed_ms=int((time.monotonic() - t0) * 1000), n_candidates=len(candidate_posts), n_ranked=len(accepted_posts))

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
