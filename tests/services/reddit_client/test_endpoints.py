"""Exception mapping tests for Reddit endpoints."""

from __future__ import annotations

import pytest
import httpx

from services.reddit_client.endpoints import fetch_comments, search_subreddit


@pytest.fixture(autouse=True)
def instant_retry(mocker):
    """Make tenacity retry waits instant so exception tests don't take minutes."""
    mocker.patch("asyncio.sleep", return_value=None)


def _client(mocker, *, side_effect) -> httpx.AsyncClient:
    """Return an AsyncMock client whose .get raises the given side_effect."""
    c = mocker.AsyncMock(spec=httpx.AsyncClient)
    c.get.side_effect = side_effect
    return c


async def test_timeout_raises(mocker):
    exc = httpx.TimeoutException("timed out")
    client = _client(mocker, side_effect=exc)

    with pytest.raises(httpx.TimeoutException):
        await search_subreddit(client, subreddit="woodworking", query="fix a drawer")

    with pytest.raises(httpx.TimeoutException):
        await fetch_comments(client, post_id="123abc")


async def test_429_raises_http_status_error(mocker):
    response = mocker.Mock()
    response.status_code = 429
    exc = httpx.HTTPStatusError("429", request=mocker.Mock(), response=response)
    client = _client(mocker, side_effect=exc)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await search_subreddit(client, subreddit="diy", query="garage organizer")
    assert exc_info.value.response.status_code == 429

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_comments(client, post_id="t3_garage456")
    assert exc_info.value.response.status_code == 429


@pytest.mark.parametrize("code", [500, 502, 503, 504])
async def test_5xx_raises_http_status_error(mocker, code):
    response = mocker.Mock()
    response.status_code = code
    exc = httpx.HTTPStatusError(str(code), request=mocker.Mock(), response=response)
    client = _client(mocker, side_effect=exc)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await search_subreddit(client, subreddit="homeimprovement", query="attic ventilation")
    assert exc_info.value.response.status_code == code

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_comments(client, post_id="t3_attic789")
    assert exc_info.value.response.status_code == code


async def test_connect_error_raises(mocker):
    exc = httpx.ConnectError("boom")
    client = _client(mocker, side_effect=exc)

    with pytest.raises(httpx.ConnectError):
        await search_subreddit(client, subreddit="diy", query="shower drain repair")

    with pytest.raises(httpx.ConnectError):
        await fetch_comments(client, post_id="t3_shelves321")
