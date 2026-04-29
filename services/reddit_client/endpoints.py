"""Raw Reddit API endpoint helpers (search, comments).

Retry policy: transient failures (timeouts, connection errors, 429, 5xx) are
retried automatically via `_reddit_retry`. Non-retryable HTTP errors (4xx other
than 429) are re-raised immediately as `httpx.HTTPStatusError`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from services.http.retry_policy import build_retry

SEARCH_PATH_TEMPLATE = "/r/{subreddit}/search"
COMMENTS_PATH_TEMPLATE = "/comments/{post_id}"


def _is_retryable_request(exc: Exception) -> bool:
    """Return True for transient request failures that warrant a retry."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return False


_reddit_retry = build_retry(is_retryable=_is_retryable_request)


@_reddit_retry
async def search_subreddit(
    client: httpx.AsyncClient,
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

    response = await client.get(
        f"https://oauth.reddit.com{SEARCH_PATH_TEMPLATE.format(subreddit=subreddit)}",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


async def paginate_search(
    client: httpx.AsyncClient,
    *,
    subreddit: str,
    query: str,
    limit: int,
) -> AsyncIterator[dict[str, Any]]:
    """Yield raw post dicts by walking the search listing."""
    remaining = max(limit, 0)
    after: str | None = None
    while remaining > 0:
        page_limit = min(remaining, 25)
        payload = await search_subreddit(
            client,
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


@_reddit_retry
async def fetch_comments(
    client: httpx.AsyncClient,
    *,
    post_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Fetch top-level comments for a submission."""
    params = {"limit": limit, "depth": 1, "sort": "top"}

    response = await client.get(
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


__all__ = [
    "search_subreddit",
    "paginate_search",
    "fetch_comments",
]
