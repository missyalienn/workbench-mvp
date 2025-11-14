"""High-level Reddit API client that wraps session management and endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from requests import Session

from .endpoints import fetch_comments, paginate_search, search_subreddit
from .session import RedditSession


class RedditClient:
    """Transport-layer facade around `RedditSession` and endpoint helpers."""

    def __init__(
        self,
        *,
        session_manager: RedditSession | None = None,
    ) -> None:
        self._session_manager = session_manager or RedditSession.from_keyring()

    def session(self) -> Session:
        """Return an authenticated session (refreshing tokens behind the scenes)."""
        return self._session_manager.get_session()

    # --- Public API -----------------------------------------------------

    def search_subreddit(
        self,
        *,
        subreddit: str,
        query: str,
        limit: int = 25,
        after: str | None = None,
    ) -> dict[str, Any]:
        """Call Reddit's search endpoint via the managed session."""
        return search_subreddit(
            self.session(),
            subreddit=subreddit,
            query=query,
            limit=limit,
            after=after,
        )

    def paginate_search(
        self,
        *,
        subreddit: str,
        query: str,
        limit: int,
    ) -> Iterator[dict[str, Any]]:
        """Iterate through subreddit search results with automatic paging."""
        return paginate_search(
            self.session(),
            subreddit=subreddit,
            query=query,
            limit=limit,
        )

    def fetch_comments(
        self,
        *,
        post_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch top-level comments for a post via the managed session."""
        return fetch_comments(
            self.session(),
            post_id=post_id,
            limit=limit,
        )

    # --------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"RedditClient(session_manager={self._session_manager!r})"
