"""Reddit-specific validation helpers.

These functions inspect raw Reddit payloads before any cleaning or
scoring happens inside the fetcher pipeline. All functions are pure and return a boolean.
"""

from __future__ import annotations

from typing import Any


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
    """Return True only when the submission is a text/self post."""
    return bool(raw_post.get("is_self"))


def is_nsfw(raw_post: dict[str, Any]) -> bool:
    """Return True when Reddit flags the submission as over_18."""
    return bool(raw_post.get("over_18"))
