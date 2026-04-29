"""Tests for the async Reddit fetch orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from common.exceptions import ExternalTimeoutError
from config.settings import settings
from agent.planner.model import SearchPlan
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.fetch.schemas import Post


def _make_plan(*, subreddits=None, search_terms=None) -> SearchPlan:
    return SearchPlan(
        plan_id=uuid4(),
        query="test query",
        search_terms=search_terms or ["test term"],
        subreddits=subreddits or ["diy"],
    )


def _mock_reddit_client(mocker, *, client):
    """Patch RedditClient so the async context manager yields `client`."""
    ctx = mocker.AsyncMock()
    ctx.__aenter__.return_value = client
    ctx.__aexit__.return_value = None
    mocker.patch("services.fetch.reddit_fetcher.RedditClient", return_value=ctx)


def _patch_filters(mocker, *, validation=True, too_short=False, seen=False):
    mocker.patch("services.fetch.reddit_fetcher.passes_post_validation", return_value=validation)
    mocker.patch("services.fetch.reddit_fetcher.is_post_too_short", return_value=too_short)
    mocker.patch("services.fetch.reddit_fetcher.has_seen_post", return_value=seen)


def _raw_post(post_id: str = "abc123") -> dict:
    return {"id": post_id, "title": "How to fix something", "selftext": "Enough body content here"}


def _make_post(post_id: str = "abc123") -> Post:
    return Post(
        id=post_id,
        subreddit="diy",
        title="How to fix something",
        selftext="Enough body content here",
        post_karma=100,
        relevance_score=0.8,
        url=f"https://reddit.com/r/diy/comments/{post_id}",
        fetched_at=1700000000.0,
    )


# --- Resilience ---

async def test_search_error(mocker):
    """Search-level failure returns an empty result without raising."""
    plan = _make_plan()
    mocker.patch.object(settings, "USE_SEMANTIC_RANKING", False)

    inner = mocker.AsyncMock()

    async def _search_raises(**kwargs):
        raise ExternalTimeoutError("rate limited")
        yield

    inner.paginate_search = _search_raises
    _mock_reddit_client(mocker, client=inner)

    result = await run_reddit_fetcher(plan=plan, post_limit=5)

    assert result.posts == []
    assert result.query == plan.query


async def test_comment_error(mocker):
    """Comment-level failure skips the post; result is empty."""
    plan = _make_plan()
    mocker.patch.object(settings, "USE_SEMANTIC_RANKING", False)

    inner = mocker.AsyncMock()

    async def _search_ok(**kwargs):
        yield _raw_post()

    inner.paginate_search = _search_ok
    inner.fetch_comments.side_effect = ExternalTimeoutError("temporary failure")

    _mock_reddit_client(mocker, client=inner)
    _patch_filters(mocker)

    result = await run_reddit_fetcher(plan=plan, post_limit=5)

    assert result.posts == []
    assert result.query == plan.query


# --- Happy path ---

async def test_happy_path(mocker):
    """Single post with successful comment fetch appears in result."""
    plan = _make_plan()
    mocker.patch.object(settings, "USE_SEMANTIC_RANKING", False)

    inner = mocker.AsyncMock()

    async def _search_ok(**kwargs):
        yield _raw_post()

    inner.paginate_search = _search_ok
    inner.fetch_comments.return_value = [{"body": "helpful comment", "score": 10}]

    _mock_reddit_client(mocker, client=inner)
    _patch_filters(mocker)
    mocker.patch("services.fetch.reddit_fetcher.filter_comments", return_value=[{"body": "helpful comment"}])
    mocker.patch("services.fetch.reddit_fetcher.build_comment_models", return_value=[MagicMock()])

    expected_post = _make_post()
    mocker.patch("services.fetch.reddit_fetcher._score_post_candidates", return_value=[expected_post])

    result = await run_reddit_fetcher(plan=plan, post_limit=5)

    assert len(result.posts) == 1
    assert result.posts[0].id == expected_post.id
    assert result.query == plan.query


# --- Filtering ---

async def test_post_skipped_when_too_short(mocker):
    """Post with a body that is too short is filtered before comment fetch."""
    plan = _make_plan()
    mocker.patch.object(settings, "USE_SEMANTIC_RANKING", False)

    inner = mocker.AsyncMock()

    async def _search_ok(**kwargs):
        yield _raw_post()

    inner.paginate_search = _search_ok
    _mock_reddit_client(mocker, client=inner)
    _patch_filters(mocker, too_short=True)

    result = await run_reddit_fetcher(plan=plan, post_limit=5)

    assert result.posts == []
    inner.fetch_comments.assert_not_called()


# --- Concurrent comment gather ---

async def test_partial_comment_failure(mocker):
    """Two posts; first comment fetch succeeds, second fails — only first survives."""
    plan = _make_plan()
    mocker.patch.object(settings, "USE_SEMANTIC_RANKING", False)

    inner = mocker.AsyncMock()

    async def _search_two_posts(**kwargs):
        yield _raw_post("post1")
        yield _raw_post("post2")

    inner.paginate_search = _search_two_posts
    # First call succeeds, second raises — asyncio.gather captures both.
    inner.fetch_comments.side_effect = [
        [{"body": "good comment", "score": 5}],
        ExternalTimeoutError("second post comment fetch failed"),
    ]

    _mock_reddit_client(mocker, client=inner)
    _patch_filters(mocker)
    mocker.patch("services.fetch.reddit_fetcher.filter_comments", return_value=[{"body": "good comment"}])
    mocker.patch("services.fetch.reddit_fetcher.build_comment_models", return_value=[MagicMock()])

    mocker.patch("services.fetch.reddit_fetcher._score_post_candidates", return_value=[_make_post("post1")])

    result = await run_reddit_fetcher(plan=plan, post_limit=5)

    assert len(result.posts) == 1
