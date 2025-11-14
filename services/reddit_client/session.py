"""Manage creation and configuration of Reddit API sessions (OAuth, headers)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import os
import keyring
import requests
import logging

from requests import Session
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE_URL = "https://oauth.reddit.com"
CLIENT_ID_SERVICE = os.getenv("REDDIT_CLIENT_ID_SERVICE", "reddit-client-id")
CLIENT_SECRET_SERVICE = os.getenv("REDDIT_CLIENT_SECRET_SERVICE", "reddit-client-secret")
USER_AGENT_SERVICE = os.getenv("REDDIT_USER_AGENT_SERVICE", "reddit-user-agent")
KEYCHAIN_LABEL = os.getenv("REDDIT_KEYCHAIN_LABEL", "reddit-dev")
DEFAULT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Workbench/1.0 by /u/chippetto90")


class RedditAuthError(RuntimeError):
    """Raised when Reddit authentication fails. Extends RuntimeError."""

class RedditSession:
    """
    Manages Reddit API authentication and session lifecycle.

    Usage:
        session_mgr = RedditSession.from_keyring()
        session = session_mgr.get_session()
        response = session.get(f"{API_BASE_URL}/r/diy/search", params={"q": "sanding"})
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

        self.session: Session = requests.Session()
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------

    def get_session(self) -> requests.Session:
        """Return a valid, authorized session (refresh token if needed)."""
        if self._token_expired():
            self._refresh_token()
        return self.session

    # ------------------------------------------------------------------

    def _token_expired(self) -> bool:
        if not self._token or not self._token_expiry:
            return True
        return datetime.now(timezone.utc) >= self._token_expiry

    def _refresh_token(self) -> None:
        """Refresh Reddit OAuth token."""
        logger.info("Refreshing Reddit OAuth token")
        try:
            response = requests.post(
                TOKEN_URL,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.user_agent},
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            raise RedditAuthError(f"Failed to fetch token: {exc}") from exc

        data = response.json()
        access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        if not access_token:
            raise RedditAuthError(f"Missing access_token in response: {data}")

        self._token = access_token
        self._token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in - self.token_refresh_buffer
        )

        self.session.headers.update({"Authorization": f"Bearer {self._token}"})
        logger.info("Reddit session authorized until %s", self._token_expiry)

    @classmethod
    def from_keyring(
        cls,
        *,
        client_id_service: str = CLIENT_ID_SERVICE,
        client_secret_service: str = CLIENT_SECRET_SERVICE,
        user_agent_service: str = USER_AGENT_SERVICE,
        label: str = KEYCHAIN_LABEL,
    ) -> "RedditSession":
        """Build a session using credentials stored in the system keychain."""
        client_id = keyring.get_password(client_id_service, label)
        client_secret = keyring.get_password(client_secret_service, label)
        user_agent = keyring.get_password(user_agent_service, label) or DEFAULT_USER_AGENT

        if not client_id or not client_secret:
            raise RedditAuthError(
                f"Missing Reddit credentials in keychain (label={label})"
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
