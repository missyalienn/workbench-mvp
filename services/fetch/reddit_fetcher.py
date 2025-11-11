
from collections.abc import Iterator
from typing import Any

from requests import Session

from agent.planner.model import SearchPlan
from agent.planner.model import SearchPlan
from .reddit_client import get_reddit_client
from .reddit_validation import (
    is_auto_moderator,
    is_created_from_ads_ui,
    is_deleted_or_removed,
    is_nsfw as raw_is_nsfw,
    is_self_post,
    is_showcase_post,
)
from .utils.text_utils import clean_text
from .utils.datetime_utils import utc_now
from .scoring import evaluate_post_relevance
from .schemas import Post, Comment, FetchResult
from config.logging_config import get_logger

# -- Constants --
MIN_POST_LENGTH = 250
MIN_COMMENT_LENGTH = 140
MIN_COMMENT_KARMA = 2
MAX_COMMENTS_PER_POST = 5

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

    for subreddit in plan.subreddits:
        for term in plan.search_terms:
            for raw_post in paginate_search(
                subreddit=subreddit,
                query=term,
                limit=post_limit,
                environment=environment,
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

                raw_comments = fetch_comments(post_id=post_id, environment=environment)
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













# Transport helpers ---------------------------------------------------------

SEARCH_PATH_TEMPLATE = "/r/{subreddit}/search"
COMMENTS_PATH_TEMPLATE = "/comments/{post_id}"


def _get_client(environment: str = "dev") -> Session:
    return get_reddit_client(environment=environment)


def search_subreddit(
    subreddit: str,
    query: str,
    limit: int = 25,
    after: str | None = None,
    environment: str = "dev",
) -> dict:
    """Call Reddit's subreddit search endpoint with required defaults."""
    params: dict[str, str | int] = {
        "q": query,
        "limit": limit,
        "restrict_sr": 1,
        "include_over_18": "false",
        "sort": "relevance",
    }
    if after:
        params["after"] = after
    session = _get_client(environment=environment)
    response = session.get(
        f"https://oauth.reddit.com{SEARCH_PATH_TEMPLATE.format(subreddit=subreddit)}",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def paginate_search(
    subreddit: str,
    query: str,
    limit: int,
    environment: str = "dev",
) -> Iterator[dict]:
    """Yield raw post dicts by walking the search listing."""
    remaining = max(limit, 0)
    after: str | None = None
    while remaining > 0:
        page_limit = min(remaining, 25)
        payload = search_subreddit(
            subreddit=subreddit,
            query=query,
            limit=page_limit,
            after=after,
            environment=environment,
        )
        children = payload.get("data", {}).get("children", [])
        if not children:
            break
        for child in children:
            yield child.get("data", {})
            remaining -= 1
            if remaining == 0:
                break
        after = payload.get("data", {}).get("after")
        if not after:
            break


def fetch_comments(
    post_id: str,
    limit: int = 50,
    environment: str = "dev",
) -> list[dict]:
    """Fetch top-level comments for a submission."""
    params = {"limit": limit, "depth": 1, "sort": "top"}
    session = _get_client(environment=environment)
    response = session.get(
        f"https://oauth.reddit.com{COMMENTS_PATH_TEMPLATE.format(post_id=post_id)}",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    comments_listing = payload[1]
    return [
        child.get("data", {})
        for child in comments_listing.get("data", {}).get("children", [])
    ]


# Helper Filtering Functions:


def filter_comments(
    post_id: str,
    raw_comments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply comment-level validation and quality checks."""
    if not raw_comments:
        return []
    filtered: list[dict[str, Any]] = []
    seen_comment_ids: set[str] = set()
    for raw_comment in raw_comments:
        comment_id = raw_comment.get("id")
        if not comment_id:
            continue
        if has_seen_comment(comment_id, seen_comment_ids):
            logger.info("Rejecting comment %s: duplicate", comment_id)
            continue
        if is_auto_moderator(raw_comment):
            logger.info("Rejecting comment %s: automoderator", comment_id)
            continue
        if is_deleted_or_removed(raw_comment.get("body")):
            logger.info("Rejecting comment %s: deleted_or_removed", comment_id)
            continue

        score = raw_comment.get("score")
        karma = int(score) if isinstance(score, (int, float)) else 0
        if karma < MIN_COMMENT_KARMA:
            logger.info("Rejecting comment %s: low_karma", comment_id)
            continue

        cleaned_body = clean_text(raw_comment.get("body", ""))
        if is_comment_too_short(cleaned_body):
            logger.info("Rejecting comment %s: too_short", comment_id)
            continue

        filtered.append(
            _build_comment_payload(
                comment_id=comment_id,
                post_id=post_id,
                cleaned_body=cleaned_body,
                comment_karma=karma,
            )
        )
    if not filtered:
        return []
    filtered.sort(key=lambda comment: comment["comment_karma"], reverse=True)
    return filtered[:MAX_COMMENTS_PER_POST]


def _build_comment_payload(
    *,
    comment_id: str,
    post_id: str,
    cleaned_body: str,
    comment_karma: int,
) -> dict[str, Any]:
    """Construct the normalized comment payload."""
    return {
        "comment_id": comment_id,
        "post_id": post_id,
        "body": cleaned_body,
        "comment_karma": comment_karma,
    }


def build_comment_models(
    filtered_comments: list[dict[str, Any]],
    fetched_at: float,
) -> list[Comment]:
    """Convert filtered comment payloads into Comment models."""
    comment_models: list[Comment] = []
    for payload in filtered_comments:
        try:
            comment_models.append(
                Comment(
                    comment_id=payload["comment_id"],
                    body=payload["body"],
                    comment_karma=payload["comment_karma"],
                    fetched_at=fetched_at,
                )
            )
        except KeyError as exc:
            logger.warning("Skipping comment payload missing %s", exc)
    return comment_models


def build_post_model(
    *,
    raw_post: dict[str, Any],
    cleaned_title: str,
    cleaned_body: str,
    relevance_score: float,
    matched_keywords: list[str],
    comments: list[Comment],
    fetched_at: float,
) -> Post:
    """Construct a Post model from cleaned data and metadata."""
    post_karma = raw_post.get("score")
    permalink = post_permalink(raw_post)
    return Post(
        id=raw_post["id"],
        title=cleaned_title,
        selftext=cleaned_body,
        post_karma=int(post_karma) if isinstance(post_karma, (int, float)) else 0,
        relevance_score=relevance_score,
        matched_keywords=matched_keywords,
        url=permalink,
        comments=comments,
        fetched_at=fetched_at,
    )


def post_permalink(raw_post: dict[str, Any]) -> str:
    """Return a canonical Reddit permalink for the submission."""
    permalink = raw_post.get("permalink")
    if isinstance(permalink, str) and permalink:
        if permalink.startswith("http"):
            return permalink
        trimmed = permalink.lstrip("/")
        return f"https://www.reddit.com/{trimmed}"

    url = raw_post.get("url")
    if isinstance(url, str) and url.startswith("http"):
        return url

    post_id = raw_post.get("id", "")
    return f"https://www.reddit.com/comments/{post_id}"


def passes_post_validation(raw_post: dict[str, Any]) -> bool:
    """Apply metadata veto checks before cleaning/scoring."""
    post_id = raw_post.get("id")
    if is_deleted_or_removed(raw_post.get("selftext")):
        logger.info("Rejecting post %s: deleted_or_removed", post_id)
        return False
    if is_auto_moderator(raw_post):
        logger.info("Rejecting post %s: automoderator", post_id)
        return False
    if is_created_from_ads_ui(raw_post):
        logger.info("Rejecting post %s: ads_ui", post_id)
        return False
    if not is_self_post(raw_post):
        logger.info("Rejecting post %s: non_self_post", post_id)
        return False
    if is_showcase_post(raw_post):
        logger.info("Rejecting post %s: showcase_post", post_id)
        return False
    if raw_is_nsfw(raw_post):
        logger.info("Rejecting post %s: nsfw", post_id)
        return False
    return True


def is_post_too_short(body: str) -> bool:
    """Return True when the cleaned post body is below the threshold."""
    trimmed = body.strip()
    return len(trimmed) < MIN_POST_LENGTH


def has_seen_post(post_id: str, seen_post_ids: set[str]) -> bool:
    """Return True if this post_id has already been processed."""
    if post_id in seen_post_ids:
        return True
    seen_post_ids.add(post_id)
    return False

def is_comment_too_short(body: str) -> bool:
    """Return True when a cleaned comment body is below the threshold."""
    trimmed = body.strip()
    return len(trimmed) < MIN_COMMENT_LENGTH
def has_seen_comment(comment_id: str, seen_comment_ids: set[str]) -> bool:
    """Return True if this comment_id has already been processed."""
    if comment_id in seen_comment_ids:
        return True
    seen_comment_ids.add(comment_id)
    return False
