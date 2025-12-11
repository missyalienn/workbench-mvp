"""Helpers that build Post/Comment models from raw Reddit payloads."""

from __future__ import annotations

from typing import Any

from .schemas import Comment, Post

# TODO: Add unit tests for builder functions to ensure payloads map to models.


def build_comment_models(
    filtered_comments: list[dict[str, Any]],
    fetched_at: float,
) -> list[Comment]:
    """Convert filtered comment payloads into Comment models."""
    comment_models: list[Comment] = []
    for payload in filtered_comments:
        try:
            comment_models.append(
                Comment(
                    comment_id=payload["comment_id"],
                    body=payload["body"],
                    comment_karma=payload["comment_karma"],
                    fetched_at=fetched_at,
                )
            )
        except KeyError as exc:
            # Keep the builder silent beyond logging in orchestrator.
            continue
    return comment_models


def build_post_model(
    *,
    raw_post: dict[str, Any],
    cleaned_title: str,
    cleaned_body: str,
    relevance_score: float,
    matched_keywords: list[str],
    comments: list[Comment],
    fetched_at: float,
) -> Post:
    """Construct a Post model from cleaned data and metadata."""
    post_karma = raw_post.get("score")
    permalink = post_permalink(raw_post)
    raw_subreddit = raw_post.get("subreddit") or ""
    subreddit = raw_subreddit.lower().lstrip("r/") if isinstance(raw_subreddit, str) else ""
    return Post(
        id=raw_post["id"],
        subreddit=subreddit,
        title=cleaned_title,
        selftext=cleaned_body,
        post_karma=int(post_karma) if isinstance(post_karma, (int, float)) else 0,
        relevance_score=relevance_score,
        matched_keywords=matched_keywords,
        url=permalink,
        comments=comments,
        fetched_at=fetched_at,
    )


def post_permalink(raw_post: dict[str, Any]) -> str:
    """Return a canonical Reddit permalink for the submission."""
    permalink = raw_post.get("permalink")
    if isinstance(permalink, str) and permalink:
        if permalink.startswith("http"):
            return permalink
        trimmed = permalink.lstrip("/")
        return f"https://www.reddit.com/{trimmed}"

    url = raw_post.get("url")
    if isinstance(url, str) and url.startswith("http"):
        return url

    post_id = raw_post.get("id", "")
    return f"https://www.reddit.com/comments/{post_id}"


def build_comment_payload(
    *,
    comment_id: str,
    post_id: str,
    cleaned_body: str,
    comment_karma: int,
) -> dict[str, Any]:
    """Construct the normalized comment payload."""
    return {
        "comment_id": comment_id,
        "post_id": post_id,
        "body": cleaned_body,
        "comment_karma": comment_karma,
    }


__all__ = [
    "build_comment_models",
    "build_post_model",
    "post_permalink",
    "build_comment_payload",
]
