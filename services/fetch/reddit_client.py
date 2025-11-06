"""Minimal Reddit REST API helper using client-credential auth.

Example:
    session = get_reddit_client()
    profile = session.get("https://oauth.reddit.com/api/v1/me").json()
"""
# TODO(mallan): Add unit tests covering token refresh and session header updates.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Final

import keyring
import requests
from requests import Session
from requests.auth import HTTPBasicAuth


TOKEN_URL: Final[str] = "https://www.reddit.com/api/v1/access_token"
API_BASE_URL: Final[str] = "https://oauth.reddit.com"

_SESSION: Session | None = None
_TOKEN: str | None = None
_TOKEN_EXPIRY: datetime | None = None


def get_reddit_client(environment: str = "dev") -> Session:
    """Return a requests.Session configured for the Reddit REST API."""
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
    token = _ensure_token(environment)
    _SESSION.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "User-Agent": _user_agent(environment),
        }
    )
    return _SESSION


def get(
    path: str,
    params: dict[str, str | int] | None = None,
    environment: str = "dev",
) -> dict:
    """Convenience helper for simple GET requests."""
    session = get_reddit_client(environment=environment)
    response = session.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _ensure_token(environment: str) -> str:
    """Return a cached access token or fetch a new one."""
    global _TOKEN, _TOKEN_EXPIRY
    now = datetime.now(tz=timezone.utc)
    if _TOKEN and _TOKEN_EXPIRY and now < _TOKEN_EXPIRY:
        return _TOKEN

    client_id = _read_secret("reddit-client-id", environment)
    client_secret = _read_secret("reddit-client-secret", environment)

    response = requests.post(
        TOKEN_URL,
        auth=HTTPBasicAuth(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": _user_agent(environment)},
        timeout=10,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Reddit auth failed ({response.status_code}): {response.text}"
        ) from exc

    payload = response.json()
    expires_in = int(payload.get("expires_in", 3600))
    _TOKEN = payload["access_token"]
    _TOKEN_EXPIRY = now + timedelta(seconds=max(expires_in - 60, 0))
    return _TOKEN


def _user_agent(environment: str) -> str:
    agent = keyring.get_password("reddit-user-agent", environment)
    return agent or "WorkbenchFetcher/1.0"


def _read_secret(key: str, environment: str) -> str:
    value = keyring.get_password(key, environment)
    if not value:
        raise RuntimeError(f"Missing keyring secret: {key} ({environment})")
    return value
