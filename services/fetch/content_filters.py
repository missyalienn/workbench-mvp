"""Content filters that run on cleaned content after raw metadata validation."""

from __future__ import annotations

from typing import Any

from config.logging_config import get_logger

# -- Constants --
MIN_POST_LENGTH = 250
MIN_COMMENT_LENGTH = 140

logger = get_logger(__name__)

# TODO: Add unit tests covering edge cases for each content filter helper.

def is_post_too_short(body: str) -> bool:
    """Return True when a cleaned post body is below the threshold."""
    trimmed = body.strip()
    return len(trimmed) < MIN_POST_LENGTH

def has_seen_post(post_id: str, seen_post_ids: set[str]) -> bool:
    """Return True if this post_id has already been processed."""
    if post_id in seen_post_ids:
        return True
    seen_post_ids.add(post_id)
    return False

def is_comment_too_short(body: str) -> bool:
    """Return True when a cleaned comment body is below the threshold."""
    trimmed = body.strip()
    return len(trimmed) < MIN_COMMENT_LENGTH

def has_seen_comment(comment_id: str, seen_comment_ids: set[str]) -> bool:
    """Return True if this comment_id has already been processed."""
    if comment_id in seen_comment_ids:
        return True
    seen_comment_ids.add(comment_id)
    return False
