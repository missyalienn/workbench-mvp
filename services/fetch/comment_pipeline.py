"""Pipeline utilities for filtering and normalizing Reddit comments."""

from __future__ import annotations

from typing import Any

from config.logging_config import get_logger
from config.settings import settings
from .content_filters import has_seen_comment, is_comment_too_short
from .reddit_validation import is_auto_moderator, is_deleted_or_removed
from .reddit_builders import build_comment_payload
from .utils.text_utils import clean_text

MIN_COMMENT_KARMA = 2

logger = get_logger(__name__)

# TODO: Add targeted tests for filter_comments to lock down karma/length rules.


def filter_comments(
    post_id: str,
    raw_comments: list[dict[str, Any]],
    max_comments: int = settings.FETCHER_MAX_COMMENTS_PER_POST,
) -> list[dict[str, Any]]:
    """Apply comment-level validation and quality checks.

    max_comments caps retained comments at fetch time. This is distinct from
    ContextBuilderConfig.max_comments_per_post, which limits comment excerpts in the LLM payload.
    """
    if not raw_comments:
        return []
    filtered: list[dict[str, Any]] = []
    seen_comment_ids: set[str] = set()
    for raw_comment in raw_comments:
        comment_id = raw_comment.get("id")
        if not comment_id:
            continue
        if has_seen_comment(comment_id, seen_comment_ids):
            logger.debug("fetch.comment_rejected", reason="duplicate", comment_id=comment_id)
            continue
        if is_auto_moderator(raw_comment):
            logger.debug("fetch.comment_rejected", reason="automoderator", comment_id=comment_id)
            continue
        if is_deleted_or_removed(raw_comment.get("body")):
            logger.debug("fetch.comment_rejected", reason="deleted_or_removed", comment_id=comment_id)
            continue

        score = raw_comment.get("score")
        karma = int(score) if isinstance(score, (int, float)) else 0
        if karma < MIN_COMMENT_KARMA:
            logger.debug("fetch.comment_rejected", reason="low_karma", comment_id=comment_id)
            continue

        cleaned_body = clean_text(raw_comment.get("body", ""))
        if is_comment_too_short(cleaned_body):
            logger.debug("fetch.comment_rejected", reason="too_short", comment_id=comment_id)
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
    return filtered[:max_comments]


__all__ = ["filter_comments"]
