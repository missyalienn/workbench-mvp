"""Raw Reddit API endpoint helpers (search, comments)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests
from requests import Session

from services.http.retry_policy import (
    RateLimitError,
    RetryableFetchError,
    fetch_with_retry,
)

SEARCH_PATH_TEMPLATE = "/r/{subreddit}/search"
COMMENTS_PATH_TEMPLATE = "/comments/{post_id}"


@fetch_with_retry()
def search_subreddit(
    session: Session,
    *,
    subreddit: str,
    query: str,
    limit: int = 25,
    after: str | None = None,
) -> dict[str, Any]:
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
    try:
        response = session.get(
            f"https://oauth.reddit.com{SEARCH_PATH_TEMPLATE.format(subreddit=subreddit)}",
            params=params,
            timeout=10,
        )
    except requests.exceptions.Timeout as exc:
        raise RetryableFetchError("Timeout during subreddit search") from exc
    except requests.exceptions.RequestException as exc:
        raise RetryableFetchError("Transport error during subreddit search") from exc

    if response.status_code == 429:
        raise RateLimitError(f"Rate limit hit for subreddit search ({subreddit})")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RetryableFetchError("HTTP error during subreddit search") from exc

    return response.json()


def paginate_search(
    session: Session,
    *,
    subreddit: str,
    query: str,
    limit: int,
) -> Iterator[dict[str, Any]]:
    """Yield raw post dicts by walking the search listing."""
    remaining = max(limit, 0)
    after: str | None = None
    while remaining > 0:
        page_limit = min(remaining, 25)
        payload = search_subreddit(
            session,
            subreddit=subreddit,
            query=query,
            limit=page_limit,
            after=after,
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

@fetch_with_retry()
def fetch_comments(
    session: Session,
    *,
    post_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Fetch top-level comments for a submission."""
    params = {"limit": limit, "depth": 1, "sort": "top"}
    try:
        response = session.get(
            f"https://oauth.reddit.com{COMMENTS_PATH_TEMPLATE.format(post_id=post_id)}",
            params=params,
            timeout=10,
        )
    except requests.exceptions.Timeout as exc:
        raise RetryableFetchError("Timeout while fetching comments") from exc
    except requests.exceptions.RequestException as exc:
        raise RetryableFetchError("Transport error while fetching comments") from exc

    if response.status_code == 429:
        raise RateLimitError(f"Rate limit hit while fetching comments ({post_id})")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RetryableFetchError("HTTP error while fetching comments") from exc

    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    comments_listing = payload[1]
    return [
        child.get("data", {})
        for child in comments_listing.get("data", {}).get("children", [])
    ]


__all__ = [
    "search_subreddit",
    "paginate_search",
    "fetch_comments",
]
