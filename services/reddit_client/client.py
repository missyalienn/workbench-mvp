"""High-level async Reddit API client that wraps session management and endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from common.exceptions import ExternalTimeoutError, InvalidResponseError, RateLimitError
from .endpoints import fetch_comments, paginate_search, search_subreddit
from .session import AsyncRedditSession


def _translate(exc: httpx.HTTPError) -> ExternalTimeoutError | RateLimitError | InvalidResponseError:
    """Translate an exhausted-retry httpx exception to a typed ExternalServiceError."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return ExternalTimeoutError(str(exc))
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 429:
            return RateLimitError(str(exc))
    return InvalidResponseError(str(exc))


class RedditClient:
    """Async transport-layer facade around `AsyncRedditSession` and endpoint helpers."""

    def __init__(
        self,
        *,
        session_manager: AsyncRedditSession | None = None,
    ) -> None:
        self._session_manager = session_manager or AsyncRedditSession.from_keyring()

    async def _client(self) -> httpx.AsyncClient:
        return await self._session_manager.get_client()

    async def aclose(self) -> None:
        await self._session_manager.aclose()

    async def __aenter__(self) -> "RedditClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    # --- Public API ---

    async def search_subreddit(
        self,
        *,
        subreddit: str,
        query: str,
        limit: int = 25,
        after: str | None = None,
    ) -> dict[str, Any]:
        try:
            return await search_subreddit(
                await self._client(),
                subreddit=subreddit,
                query=query,
                limit=limit,
                after=after,
            )
        except httpx.HTTPError as exc:
            raise _translate(exc) from exc

    async def paginate_search(
        self,
        *,
        subreddit: str,
        query: str,
        limit: int,
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            async for post in paginate_search(
                await self._client(),
                subreddit=subreddit,
                query=query,
                limit=limit,
            ):
                yield post
        except httpx.HTTPError as exc:
            raise _translate(exc) from exc

    async def fetch_comments(
        self,
        *,
        post_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        try:
            return await fetch_comments(
                await self._client(),
                post_id=post_id,
                limit=limit,
            )
        except httpx.HTTPError as exc:
            raise _translate(exc) from exc

    def __repr__(self) -> str:
        return f"RedditClient(session_manager={self._session_manager!r})"
