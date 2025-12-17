"""Unit tests for services.summarizer.selector."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from services.fetch.schemas import Comment, FetchResult, Post
from services.selector.config import SelectorConfig
from services.summarizer.config import SummarizerConfig
from services.summarizer.selector import (
    build_comment_excerpts,
    build_post_payload,
    build_summarize_request,
    select_posts,
)


def make_cfg(
    max_posts: int = 2,
    max_comments_per_post: int = 2,
    max_post_chars: int = 200,
    max_comment_chars: int = 80,
) -> SelectorConfig:
    """Factory for SelectorConfig with sensible defaults."""

    return SelectorConfig(
        max_posts=max_posts,
        max_comments_per_post=max_comments_per_post,
        max_post_chars=max_post_chars,
        max_comment_chars=max_comment_chars,
    )


def make_comment(comment_id: str, body: str, comment_karma: int) -> Comment:
    """Factory for Comment."""

    return Comment(
        comment_id=comment_id,
        body=body,
        comment_karma=comment_karma,
        fetched_at=0.0,
    )


def make_post(
    post_id: str,
    *,
    relevance_score: float,
    post_karma: int,
    subreddit: str = "test subreddit",
    selftext: str = "Body",
    title: str = "Title",
    url: str = "https://reddit.com/r/test/comments/slug/title",
    matched_keywords: list[str] | None = None,
    comments: list[Comment] | None = None,
) -> Post:
    """Factory for Post."""

    return Post(
        id=post_id,
        subreddit=subreddit,
        title=title,
        selftext=selftext,
        post_karma=post_karma,
        relevance_score=relevance_score,
        matched_keywords=matched_keywords or [],
        url=url,
        comments=comments or [],
        fetched_at=0.0,
        source="reddit",
    )


def make_fetch_result(
    posts: list[Post],
    *,
    plan_id: UUID | None = None,
    query: str = "best tools",
) -> FetchResult:
    """Factory for FetchResult."""

    return FetchResult(
        query=query,
        plan_id=plan_id or uuid4(),
        search_terms=["best tools"],
        subreddits=["test"],
        source="reddit",
        fetched_at=0.0,
        posts=posts,
    )


def test_select_posts_ranks_by_score() -> None:
    cfg = make_cfg(max_posts=2)
    posts = [
        make_post("high_relevance_high_karma", relevance_score=0.8, post_karma=50),
        make_post("lower_relevance_high_karma", relevance_score=0.5, post_karma=500),
        make_post("high_relevance_low_karma", relevance_score=0.8, post_karma=5),
    ]

    result = select_posts(make_fetch_result(posts), cfg)

    assert [post.id for post in result] == [
        "high_relevance_high_karma",
        "high_relevance_low_karma",
    ]


def test_build_comment_excerpts_limits_and_truncates() -> None:
    cfg = make_cfg(max_comments_per_post=2, max_comment_chars=5)
    comments = [
        make_comment("c_low", "abcdef", comment_karma=5),
        make_comment("c_high", "hi", comment_karma=20),
        make_comment("c_ignored", "later", comment_karma=1),
    ]

    excerpts = build_comment_excerpts(comments, cfg)

    assert excerpts == ["hi", "abcde"]


def test_build_post_payload_trims_body() -> None:
    cfg = make_cfg(max_comments_per_post=1, max_comment_chars=3, max_post_chars=4)
    comments = [
        make_comment("c1", "comment body", comment_karma=100),
        make_comment("c2", "ignored", comment_karma=1),
    ]
    post = make_post(
        "post_id_1",
        subreddit= "test subreddit",
        relevance_score=0.9,
        post_karma=10,
        selftext="123456",
        url="https://reddit.com/r/home/comments/slug/title",
        comments=comments,
    )

    payload = build_post_payload(post, cfg)

    assert payload.body_excerpt == "1234"
    assert payload.top_comment_excerpts == ["com"]
    assert payload.num_comments == 2
    assert payload.subreddit == "test subreddit"


def test_build_post_payload_rejects_invalid_url() -> None:
    cfg = make_cfg()
    post = make_post(
        "bad_url_post",
        relevance_score=0.5,
        post_karma=5,
        url="not-a-valid-url",
    )

    with pytest.raises(ValidationError):
        build_post_payload(post, cfg)


def test_build_summarize_request_copies_metadata() -> None:
    cfg = make_cfg(max_posts=1)
    posts = [
        make_post("p1", relevance_score=0.9, post_karma=10),
        make_post("p2", relevance_score=0.8, post_karma=999),
    ]
    fetch_result = make_fetch_result(posts, query="how to test?", plan_id=uuid4())

    summarizer_cfg = SummarizerConfig(
        summary_char_budget=1024,
        max_highlights=5,
        max_cautions=3,
    )
    request = build_summarize_request(fetch_result, cfg, prompt_version="v1", summarizer_cfg=summarizer_cfg)

    assert request.query == "how to test?"
    assert request.plan_id == fetch_result.plan_id
    assert request.prompt_version == "v1"
    assert request.max_posts == cfg.max_posts
    assert len(request.post_payloads) == 1
    assert request.post_payloads[0].post_id == "p1"
    assert request.summary_char_budget == summarizer_cfg.summary_char_budget
    assert request.max_highlights == summarizer_cfg.max_highlights
    assert request.max_cautions == summarizer_cfg.max_cautions
