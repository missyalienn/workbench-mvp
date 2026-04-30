"""Unit tests for synthesizer prompt construction."""

from __future__ import annotations

from uuid import uuid4

from services.synthesizer.llm_execution.prompt_builder import build_messages
from services.synthesizer.models import EvidenceRequest, PostPayload


def test_build_messages_does_not_request_thread_echoing() -> None:
    request = EvidenceRequest(
        query="how to patch drywall",
        plan_id=uuid4(),
        post_payloads=[
            PostPayload(
                post_id="p1",
                subreddit="diy",
                title="Patch drywall after outlet move",
                url="https://example.com/post",
                body_excerpt="body",
                top_comment_excerpts=["comment"],
                post_karma=42,
                num_comments=6,
                relevance_score=0.88,
                matched_keywords=[],
            )
        ],
        prompt_version="v3",
        max_posts=5,
        max_comments_per_post=2,
        max_post_chars=200,
        max_comment_chars=100,
        summary_char_budget=500,
        max_highlights=3,
        max_cautions=2,
    )

    messages = build_messages(request)
    system_content = messages[0].content

    assert "ThreadEvidence" not in system_content
    assert "ranked best-to-worst" not in system_content
    assert "copy post_id/title/subreddit/url/relevance_score exactly from payload" not in system_content
