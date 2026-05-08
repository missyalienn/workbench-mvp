"""Unit tests for synthesizer prompt construction."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from services.synthesizer.llm_execution.prompt_builder import build_messages
from services.synthesizer.models import EvidenceRequest, PostPayload


def _make_request(*, prompt_version: str = "v3") -> EvidenceRequest:
    return EvidenceRequest(
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
        prompt_version=prompt_version,
        max_posts=5,
        max_comments_per_post=2,
        max_post_chars=200,
        max_comment_chars=100,
        summary_char_budget=500,
    )


def test_build_messages_does_not_request_thread_echoing() -> None:
    request = _make_request(prompt_version="v3")

    messages = build_messages(request)
    system_content = messages[0].content

    assert "ThreadEvidence" not in system_content
    assert "ranked best-to-worst" not in system_content
    assert "copy post_id/title/subreddit/url/relevance_score exactly from payload" not in system_content


def test_build_messages_includes_post_karma_and_num_comments_in_user_payload() -> None:
    request = EvidenceRequest(
        query="best anchors for plaster wall shelves",
        plan_id=uuid4(),
        post_payloads=[
            PostPayload(
                post_id="p1",
                subreddit="homeimprovement",
                title="Shelf anchors for old plaster walls",
                url="https://example.com/post",
                body_excerpt="body",
                top_comment_excerpts=["comment"],
                post_karma=128,
                num_comments=14,
                relevance_score=0.91,
                matched_keywords=["plaster", "anchors"],
            )
        ],
        prompt_version="v3",
        max_posts=5,
        max_comments_per_post=2,
        max_post_chars=200,
        max_comment_chars=100,
        summary_char_budget=500,
    )

    messages = build_messages(request)
    user_payload = json.loads(messages[1].content)
    post_payload = user_payload["post_payloads"][0]

    assert post_payload["post_karma"] == 128
    assert post_payload["num_comments"] == 14
    assert "matched_keywords" not in post_payload


def test_build_messages_uses_original_v3_limitations_prompt() -> None:
    messages = build_messages(_make_request(prompt_version="v3"))
    system_content = messages[0].content

    assert "- limitations: 1-2 short strings explaining thin/empty evidence" in system_content
    assert "Describe only coverage gaps directly tied to the user's query" in system_content
    assert "Only 4 threads found; most discuss metal studs vs. standard drywall." not in system_content


def test_build_messages_uses_current_v4_limitations_prompt() -> None:
    messages = build_messages(_make_request(prompt_version="v4"))
    system_content = messages[0].content

    assert "Limitations rules:" in system_content
    assert "Describe only coverage gaps directly tied to the user's query" in system_content
    assert '"limitations": [' in system_content
    assert "prompt_version: must match request.prompt_version exactly" not in system_content
    assert '"prompt_version":' not in system_content


def test_build_messages_rejects_unsupported_prompt_version() -> None:
    with pytest.raises(ValueError, match="Unsupported prompt_version: v5"):
        build_messages(_make_request(prompt_version="v5"))
