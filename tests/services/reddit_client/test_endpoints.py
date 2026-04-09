"""Exception mapping tests for Reddit endpoints."""

from __future__ import annotations

import pytest
import requests

from services.reddit_client.endpoints import fetch_comments, search_subreddit


class TestSession:
    """Simple session stub; `.get` gets patched per test."""

    def get(self, *args, **kwargs):
        raise NotImplementedError("Patched per test")


# Timeout -> requests.exceptions.Timeout
def test_timeout_raises(mocker):
    session = TestSession()
    mocker.patch.object(session, "get", side_effect=requests.exceptions.Timeout())

    with pytest.raises(requests.exceptions.Timeout):
        search_subreddit(session, subreddit="woodworking", query="fix a drawer")

    with pytest.raises(requests.exceptions.Timeout):
        fetch_comments(session, post_id="123abc")


# HTTP 429 -> requests.exceptions.HTTPError (status_code=429, retried then re-raised)
def test_429_raises_http_error(mocker):
    session = TestSession()
    response = mocker.Mock(status_code=429)
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mocker.patch.object(session, "get", return_value=response)

    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        search_subreddit(session, subreddit="diy", query="garage organizer")
    assert exc_info.value.response.status_code == 429

    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        fetch_comments(session, post_id="t3_garage456")
    assert exc_info.value.response.status_code == 429


# HTTP 5xx -> requests.exceptions.HTTPError (retried then re-raised)
@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_5xx_raises_http_error(mocker, code):
    session = TestSession()
    response = mocker.Mock(status_code=code)
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mocker.patch.object(session, "get", return_value=response)

    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        search_subreddit(session, subreddit="homeimprovement", query="attic ventilation")
    assert exc_info.value.response.status_code == code

    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        fetch_comments(session, post_id="t3_attic789")
    assert exc_info.value.response.status_code == code


# Connection error -> requests.exceptions.ConnectionError (retried then re-raised)
def test_connection_error_raises(mocker):
    session = TestSession()
    mocker.patch.object(session, "get", side_effect=requests.exceptions.ConnectionError("boom"))

    with pytest.raises(requests.exceptions.ConnectionError):
        search_subreddit(session, subreddit="diy", query="shower drain repair")

    with pytest.raises(requests.exceptions.ConnectionError):
        fetch_comments(session, post_id="t3_shelves321")
