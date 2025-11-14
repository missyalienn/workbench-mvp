"""
Reddit validation helpers. Used to validate raw Reddit payloads before cleaning or content filtering downstream. 
All functions are pure and return a boolean.
"""

from __future__ import annotations

from typing import Any

from .keyword_groups import NEGATIVE_KEYWORDS
from config.logging_config import get_logger

logger = get_logger(__name__)

SHOWCASE_KEYWORDS = tuple(
    keyword.lower()
    for keyword in NEGATIVE_KEYWORDS.get("showcase_brag", {}).get("keywords", [])
)
SHOWCASE_KARMA_THRESHOLD = 150


def is_deleted_or_removed(text: str | None) -> bool:
    """Return True when the body/selftext is missing or marked deleted."""
    if text is None:
        return True
    normalized = text.strip().lower()
    return normalized in {"", "[deleted]", "[removed]"}


def is_auto_moderator(raw_item: dict[str, Any]) -> bool:
    """Return True when the author is AutoModerator."""
    return raw_item.get("author") == "AutoModerator"


def is_created_from_ads_ui(raw_post: dict[str, Any]) -> bool:
    """Return True for sponsored posts created via Reddit's ads UI."""
    return bool(raw_post.get("is_created_from_ads_ui"))


def is_self_post(raw_post: dict[str, Any]) -> bool:
    """Return True when the submission is text-only or an allowed image/gallery."""
    if raw_post.get("is_self"):
        return True
    post_hint = raw_post.get("post_hint")
    if isinstance(post_hint, str) and post_hint.lower() == "image":
        return True
    return bool(raw_post.get("is_gallery"))


def is_nsfw(raw_post: dict[str, Any]) -> bool:
    """Return True when Reddit flags the submission as over_18."""
    return bool(raw_post.get("over_18"))


def is_showcase_post(raw_post: dict[str, Any]) -> bool:
    """Return True when the post matches showcase heuristics (image + brag + high karma)."""
    if not SHOWCASE_KEYWORDS:
        return False
    if not _has_image_hint(raw_post):
        return False
    if not _has_showcase_phrase(raw_post):
        return False
    return _has_high_karma(raw_post)


def _has_image_hint(raw_post: dict[str, Any]) -> bool:
    post_hint = raw_post.get("post_hint")
    if isinstance(post_hint, str) and post_hint.lower() == "image":
        return True
    return bool(raw_post.get("is_gallery"))


def _has_showcase_phrase(raw_post: dict[str, Any]) -> bool:
    text = f"{raw_post.get('title', '')} {raw_post.get('selftext', '')}".lower()
    return any(keyword in text for keyword in SHOWCASE_KEYWORDS)


def _has_high_karma(raw_post: dict[str, Any]) -> bool:
    score = raw_post.get("score")
    if isinstance(score, (int, float)):
        return score >= SHOWCASE_KARMA_THRESHOLD
    return False


def passes_post_validation(raw_post: dict[str, Any]) -> bool:
    """Apply metadata veto checks before cleaning/scoring."""
    post_id = raw_post.get("id")
    if is_deleted_or_removed(raw_post.get("selftext")):
        logger.info("Rejecting post %s: deleted_or_removed", post_id)
        return False
    if is_auto_moderator(raw_post):
        logger.info("Rejecting post %s: automoderator", post_id)
        return False
    if is_created_from_ads_ui(raw_post):
        logger.info("Rejecting post %s: ads_ui", post_id)
        return False
    if not is_self_post(raw_post):
        logger.info("Rejecting post %s: non_self_post", post_id)
        return False
    if is_showcase_post(raw_post):
        logger.info("Rejecting post %s: showcase_post", post_id)
        return False
    if is_nsfw(raw_post):
        logger.info("Rejecting post %s: nsfw", post_id)
        return False
    return True