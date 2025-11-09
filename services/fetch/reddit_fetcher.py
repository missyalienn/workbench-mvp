
from collections.abc import Iterator
from typing import Any

from requests import Session

from .reddit_client import get_reddit_client
from .reddit_validation import (
    is_auto_moderator,
    is_created_from_ads_ui,
    is_deleted_or_removed,
    is_nsfw as raw_is_nsfw,
    is_self_post,
)
from .utils.text_utils import clean_text
from .scoring import evaluate_post_relevance
from .schemas import Post, Comment, FetchResult
from config.logging_config import get_logger

# -- Constants --
MIN_POST_LENGTH = 250
MIN_COMMENT_LENGTH = 140

logger = get_logger(__name__)

"""
RedditFetcher pipeline contract (implementation TBD).

The fetcher turns a Planner-produced `SearchPlan` into a `FetchResult`
that downstream agents use to build a Guided Summary (curated links,
recurring themes, and a cautious action outline). 
"""

def run_reddit_fetcher(search_terms: list[str], subreddits: list[str], limit: int) -> FetchResult:
   """
   Orchestator function that will call the other helper functions.
   """
   pass

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
        if comment_id in seen_comment_ids:
            logger.info("Rejecting comment %s: duplicate", comment_id)
            continue
        if is_auto_moderator(raw_comment):
            logger.info("Rejecting comment %s: automoderator", comment_id)
            continue
        if is_deleted_or_removed(raw_comment.get("body")):
            logger.info("Rejecting comment %s: deleted_or_removed", comment_id)
            continue

        cleaned_body = clean_text(raw_comment.get("body", ""))
        if is_comment_too_short(cleaned_body):
            logger.info("Rejecting comment %s: too_short", comment_id)
            continue

        seen_comment_ids.add(comment_id)
        filtered.append(
            _build_comment_payload(
                comment_id=comment_id,
                post_id=post_id,
                cleaned_body=cleaned_body,
                raw_comment=raw_comment,
            )
        )
    return filtered


def _build_comment_payload(
    *,
    comment_id: str,
    post_id: str,
    cleaned_body: str,
    raw_comment: dict[str, Any],
) -> dict[str, Any]:
    """Construct the normalized comment payload."""
    score = raw_comment.get("score")
    karma = int(score) if isinstance(score, (int, float)) else 0
    return {
        "comment_id": comment_id,
        "post_id": post_id,
        "body": cleaned_body,
        "comment_karma": karma,
    }


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
    if raw_is_nsfw(raw_post):
        logger.info("Rejecting post %s: nsfw", post_id)
        return False
    return True


def is_post_too_short(body: str) -> bool:
   """
   Check if the post body is too short.
   """
   trimmed = body.strip()
   return len(trimmed) < MIN_POST_LENGTH

   # Dedupe logic (post-level):
   if post_id in seen_post_ids:
      logger.info("Rejecting post %s: duplicate", post_id)
      return True
   seen_post_ids.add(post_id)
   return False

def is_comment_too_short(body: str) -> bool:
   """
   Check if the comment body is too short.
   """
   trimmed = body.strip()
   return len(trimmed) < MIN_COMMENT_LENGTH
