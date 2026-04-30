"""Unit tests for the API pipeline assembly helpers."""

from __future__ import annotations

from uuid import uuid4

from api.models import SearchPlan
from api.pipeline import _build_client_threads, _to_client_response
from services.synthesizer.models import EvidenceRequest, EvidenceResult, PostPayload


class _PlanStub:
    def __init__(self, *, search_terms: list[str], subreddits: list[str]) -> None:
        self.search_terms = search_terms
        self.subreddits = subreddits


def _make_post_payload(
    post_id: str,
    *,
    title: str,
    subreddit: str,
    url: str,
    relevance_score: float,
) -> PostPayload:
    return PostPayload(
        post_id=post_id,
        subreddit=subreddit,
        title=title,
        url=url,
        body_excerpt="body",
        top_comment_excerpts=["comment"],
        post_karma=10,
        num_comments=3,
        relevance_score=relevance_score,
        matched_keywords=[],
    )


def _make_request(post_payloads: list[PostPayload]) -> EvidenceRequest:
    return EvidenceRequest(
        query="query",
        plan_id=uuid4(),
        post_payloads=post_payloads,
        prompt_version="v3",
        max_posts=5,
        max_comments_per_post=2,
        max_post_chars=200,
        max_comment_chars=100,
        summary_char_budget=500,
        max_highlights=3,
        max_cautions=2,
    )


def test_build_client_threads_preserves_context_order() -> None:
    post_payloads = [
        _make_post_payload(
            "p1",
            title="First title",
            subreddit="diy",
            url="https://example.com/1",
            relevance_score=0.9,
        ),
        _make_post_payload(
            "p2",
            title="Second title",
            subreddit="homeimprovement",
            url="https://example.com/2",
            relevance_score=0.8,
        ),
    ]

    threads = _build_client_threads(post_payloads)

    assert [thread.rank for thread in threads] == [1, 2]
    assert [thread.title for thread in threads] == ["First title", "Second title"]
    assert [thread.relevance_score for thread in threads] == [0.9, 0.8]


def test_to_client_response_uses_request_post_payloads_for_threads() -> None:
    request = _make_request(
        [
            _make_post_payload(
                "p1",
                title="Context-ranked title",
                subreddit="diy",
                url="https://example.com/context",
                relevance_score=0.95,
            )
        ]
    )
    result = EvidenceResult(
        status="partial",
        summary="Evidence is mixed but points in one direction.",
        limitations=["Only one relevant source was found."],
        prompt_version="v3",
    )
    plan = _PlanStub(search_terms=["floor squeak"], subreddits=["DIY"])

    response = _to_client_response(plan, request, result)

    assert response.search_plan == SearchPlan(
        search_terms=["floor squeak"],
        subreddits=["DIY"],
    )
    assert response.status == "partial"
    assert response.summary == result.summary
    assert response.limitations == result.limitations
    assert len(response.threads) == 1
    assert response.threads[0].title == "Context-ranked title"
    assert response.threads[0].url == "https://example.com/context"
    assert response.threads[0].relevance_score == 0.95
