"""Resilience tests for the Reddit fetch orchestrator."""

from __future__ import annotations

from uuid import uuid4

from agent.planner.model import SearchPlan
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.http.retry_policy import RateLimitError, RetryableFetchError


def _make_plan() -> SearchPlan:
    return SearchPlan(
        plan_id=uuid4(),
        query="test query",
        search_terms=["test term"],
        subreddits=["diy"],
        notes="unit test plan",
    )


def test_search_error(mocker):
    """Search-level RateLimitError/RetryableFetchError should be handled and return an empty result."""
    plan = _make_plan()

    mock_client = mocker.Mock()
    mock_client.paginate_search.side_effect = RateLimitError("rate limited")

    mocker.patch("services.fetch.reddit_fetcher.RedditClient", return_value=mock_client)

    result = run_reddit_fetcher(plan=plan, post_limit=5)

    assert result.posts == []
    assert result.query == plan.query


def test_comment_error(mocker):
    """Comment-level RateLimitError/RetryableFetchError should be handled and skip the post."""
    plan = _make_plan()

    mock_client = mocker.Mock()
    mock_client.paginate_search.return_value = iter(
        [
            {
                "id": "abc123",
                "title": "How to fix something",
                "selftext": "Body content",
            }
        ]
    )
    mock_client.fetch_comments.side_effect = RetryableFetchError("temporary failure")

    mocker.patch("services.fetch.reddit_fetcher.RedditClient", return_value=mock_client)
    mocker.patch("services.fetch.reddit_fetcher.passes_post_validation", return_value=True)
    mocker.patch("services.fetch.reddit_fetcher.is_post_too_short", return_value=False)
    mocker.patch("services.fetch.reddit_fetcher.has_seen_post", return_value=False)
    mocker.patch(
        "services.fetch.reddit_fetcher.evaluate_post_relevance",
        return_value=(1.0, ["keyword"], None, True),
    )

    result = run_reddit_fetcher(plan=plan, post_limit=5)

    assert result.posts == []
    assert result.query == plan.query
