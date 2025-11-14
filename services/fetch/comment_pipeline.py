"""Pipeline utilities for filtering and normalizing Reddit comments."""

from __future__ import annotations

from typing import Any

from config.logging_config import get_logger
from .content_filters import has_seen_comment, is_comment_too_short
from .reddit_validation import is_auto_moderator, is_deleted_or_removed
from .reddit_builders import build_comment_payload
from .utils.text_utils import clean_text

MIN_COMMENT_KARMA = 2
MAX_COMMENTS_PER_POST = 5

logger = get_logger(__name__)

# TODO: Add targeted tests for filter_comments to lock down karma/length rules.


def filter_comments(
    post_id: str,
    raw_comments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply comment-level validation and quality checks."""
    if not raw_comments:
        return []
    filtered: list[dict[str, Any]] = []
    seen_comment_ids: set[str] = set()
    for raw_comment in raw_comments:
        comment_id = raw_comment.get("id")
        if not comment_id:
            continue
        if has_seen_comment(comment_id, seen_comment_ids):
            logger.info("Rejecting comment %s: duplicate", comment_id)
            continue
        if is_auto_moderator(raw_comment):
            logger.info("Rejecting comment %s: automoderator", comment_id)
            continue
        if is_deleted_or_removed(raw_comment.get("body")):
            logger.info("Rejecting comment %s: deleted_or_removed", comment_id)
            continue

        score = raw_comment.get("score")
        karma = int(score) if isinstance(score, (int, float)) else 0
        if karma < MIN_COMMENT_KARMA:
            logger.info("Rejecting comment %s: low_karma", comment_id)
            continue

        cleaned_body = clean_text(raw_comment.get("body", ""))
        if is_comment_too_short(cleaned_body):
            logger.info("Rejecting comment %s: too_short", comment_id)
            continue

        filtered.append(
            build_comment_payload(
                comment_id=comment_id,
                post_id=post_id,
                cleaned_body=cleaned_body,
                comment_karma=karma,
            )
        )
    if not filtered:
        return []
    filtered.sort(key=lambda comment: comment["comment_karma"], reverse=True)
    return filtered[:MAX_COMMENTS_PER_POST]


__all__ = ["filter_comments"]
