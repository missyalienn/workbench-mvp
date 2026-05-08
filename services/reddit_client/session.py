"""Manage creation and configuration of async Reddit API sessions (OAuth, headers)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import keyring

from common.exceptions import AuthError
from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE_URL = "https://oauth.reddit.com"
DEFAULT_USER_AGENT = settings.REDDIT_USER_AGENT


class AsyncRedditSession:
    """
    Manages Reddit API authentication and async session lifecycle.

    Usage:
        session_mgr = AsyncRedditSession.from_keyring()
        client = await session_mgr.get_client()
        response = await client.get(f"{API_BASE_URL}/r/diy/search", params={"q": "sanding"})
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str = DEFAULT_USER_AGENT,
        token_refresh_buffer: int = 60,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.token_refresh_buffer = token_refresh_buffer

        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }
        )
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> httpx.AsyncClient:
        """Return a valid, authorized client (refresh token if needed)."""
        if not self._token_expired():
            return self._client
        async with self._lock:
            if self._token_expired():
                await self._refresh_token()
        return self._client

    async def aclose(self) -> None:
        await self._client.aclose()

    def _token_expired(self) -> bool:
        if not self._token or not self._token_expiry:
            return True
        return datetime.now(timezone.utc) >= self._token_expiry

    async def _refresh_token(self) -> None:
        """Refresh Reddit OAuth token."""
        logger.info("reddit.token_refresh")
        try:
            async with httpx.AsyncClient() as tmp:
                response = await tmp.post(
                    TOKEN_URL,
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"User-Agent": self.user_agent},
                    timeout=10,
                )
            response.raise_for_status()
        except Exception as exc:
            raise AuthError(f"Failed to fetch token: {exc}") from exc

        data = response.json()
        access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        if not access_token:
            raise AuthError(f"Missing access_token in response: {data}")

        self._token = access_token
        self._token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in - self.token_refresh_buffer
        )
        self._client.headers["Authorization"] = f"Bearer {self._token}"
        logger.info("reddit.session_authorized", expires_at=str(self._token_expiry))

    @classmethod
    def from_env(cls) -> "AsyncRedditSession":
        """Build a session using settings-backed environment credentials."""
        client_id = settings.REDDIT_CLIENT_ID
        client_secret = settings.REDDIT_CLIENT_SECRET
        user_agent = settings.REDDIT_USER_AGENT

        if not client_id or not client_secret:
            missing = [
                name
                for name, value in (
                    ("REDDIT_CLIENT_ID", client_id),
                    ("REDDIT_CLIENT_SECRET", client_secret),
                )
                if not value
            ]
            logger.error("reddit.missing_env_credentials", missing=missing)
            raise AuthError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

    @classmethod
    def from_keyring(
        cls,
        *,
        client_id_service: str = settings.REDDIT_CLIENT_ID_SERVICE,
        client_secret_service: str = settings.REDDIT_CLIENT_SECRET_SERVICE,
        user_agent_service: str = settings.REDDIT_USER_AGENT_SERVICE,
        label: str = settings.REDDIT_KEYCHAIN_LABEL,
    ) -> "AsyncRedditSession":
        """Build a session using credentials stored in the system keychain."""
        client_id = keyring.get_password(client_id_service, label)
        client_secret = keyring.get_password(client_secret_service, label)
        user_agent = keyring.get_password(user_agent_service, label) or DEFAULT_USER_AGENT

        if not client_id or not client_secret:
            logger.error(
                "reddit.missing_credentials",
                label=label,
                fix="Run: keyring set reddit-client-id <label> <id> && keyring set reddit-client-secret <label> <secret>",
            )
            raise AuthError(
                f"Missing Reddit API credentials in keychain (label='{label}'). "
                f"Fix: keyring set reddit-client-id {label} <id> && keyring set reddit-client-secret {label} <secret>"
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
