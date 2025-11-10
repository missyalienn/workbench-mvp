"""Keyword-based relevance scoring for Reddit posts."""

from __future__ import annotations

import re
from typing import Iterable, List, Tuple

from config.logging_config import get_logger

from .keyword_groups import (
    KEYWORD_GROUPS,
    KEYWORD_WEIGHTS,
    MIN_POST_SCORE,
    NEGATIVE_KEYWORDS,
)

logger = get_logger(__name__)

_SUFFIXES: Tuple[str, ...] = ("", "s", "ed", "ing")


def evaluate_post_relevance(
    post_id: str,
    title: str,
    body: str,
) -> tuple[float, list[str], list[str], bool]:
    """Compute keyword relevance score and log the decision."""
    combined_text = f"{title or ''} {body or ''}".lower()

    positive_matches: list[str] = []
    negative_matches: list[str] = []
    relevance_score = 0.0

    for group_name, group in KEYWORD_GROUPS.items():
        weight = KEYWORD_WEIGHTS.get(group_name, 0.0)
        matches = _find_matches(group["keywords"], combined_text)
        if matches:
            relevance_score += weight
            positive_matches.extend(matches)

    if not positive_matches:
        for group_name, group in NEGATIVE_KEYWORDS.items():
            weight = KEYWORD_WEIGHTS.get(group_name, 0.0)
            matches = _find_matches(group["keywords"], combined_text)
            if matches:
                relevance_score += weight
                negative_matches.extend(matches)

    passed_threshold = relevance_score >= MIN_POST_SCORE
    decision_reason = _decision_reason(
        passed_threshold,
        positive_matches,
        negative_matches,
    )

    log_message = (
        "Post accepted by keyword scoring"
        if passed_threshold
        else "Post rejected by keyword scoring"
    )

    logger.debug(
        log_message,
        extra={
            "post_id": post_id,
            "relevance_score": relevance_score,
            "matched_keywords": ", ".join(positive_matches),
            "negative_keywords": ", ".join(negative_matches),
            "threshold": MIN_POST_SCORE,
            "decision": "accepted" if passed_threshold else "rejected",
            "decision_reason": decision_reason,
        },
    )

    return relevance_score, positive_matches, negative_matches, passed_threshold


def _find_matches(keywords: Iterable[str], text: str) -> List[str]:
    matches: list[str] = []
    for keyword in keywords:
        normalized = keyword.lower()
        for variant in _expand_variants(normalized):
            if _contains_variant(text, variant):
                matches.append(keyword)
                break
    return matches


def _expand_variants(keyword: str) -> Tuple[str, ...]:
    if " " in keyword:
        return (keyword,)
    return tuple(f"{keyword}{suffix}" for suffix in _SUFFIXES)


def _contains_variant(text: str, variant: str) -> bool:
    if not variant:
        return False
    pattern = rf"\b{re.escape(variant)}\b"
    return bool(re.search(pattern, text))


def _decision_reason(
    passed_threshold: bool,
    positive_matches: List[str],
    negative_matches: List[str],
) -> str:
    if passed_threshold:
        return "passed_threshold"
    if negative_matches and not positive_matches:
        return "negative_veto"
    return "below_threshold"
