"""Exception mapping tests for Reddit endpoints."""

from __future__ import annotations

import pytest
import requests

from services.http.retry_policy import RateLimitError, RetryableFetchError
from services.reddit_client.endpoints import search_subreddit, fetch_comments


class TestSession:
    """Simple session stub; `.get` gets patched per test."""

    def get(self, *args, **kwargs):
        raise NotImplementedError("Patched per test")


# TIMEOUT -> RetryableFetchError
def test_timeout_maps_to_retryable(mocker):
    session = TestSession()
    mocker.patch.object(session, "get", side_effect=requests.exceptions.Timeout())

    with pytest.raises(RetryableFetchError):
        search_subreddit(
            session,
            subreddit="woodworking",
            query="fix a drawer",
        )

    with pytest.raises(RetryableFetchError):
        fetch_comments(
            session,
            post_id="123abc",
        )


# HTTP 429 -> RateLimitError
def test_429_maps_to_rate_limit(mocker):
    session = TestSession()
    response = mocker.Mock(status_code=429)
    response.raise_for_status.return_value = None
    mocker.patch.object(session, "get", return_value=response)

    with pytest.raises(RateLimitError):
        search_subreddit(
            session,
            subreddit="diy",
            query="garage organizer",
        )

    with pytest.raises(RateLimitError):
        fetch_comments(
            session,
            post_id="t3_garage456",
        )


# HTTP 5xx -> RetryableFetchError
@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_5xx_maps_to_retryable(mocker, code):
    session = TestSession()
    response = mocker.Mock(status_code=code)
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mocker.patch.object(session, "get", return_value=response)

    with pytest.raises(RetryableFetchError):
        search_subreddit(
            session,
            subreddit="homeimprovement",
            query="attic ventilation",
        )

    with pytest.raises(RetryableFetchError):
        fetch_comments(
            session,
            post_id="t3_attic789",
        )


# Network errors -> RetryableFetchError
def test_network_error_maps_to_retryable(mocker):
    session = TestSession()
    mocker.patch.object(session, "get", side_effect=requests.RequestException("boom"))

    with pytest.raises(RetryableFetchError):
        search_subreddit(
            session,
            subreddit="diy",
            query="shower drain repair",
        )

    with pytest.raises(RetryableFetchError):
        fetch_comments(
            session,
            post_id="t3_shelves321",
        )
