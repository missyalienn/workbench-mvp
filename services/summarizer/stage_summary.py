"""Stage-boundary summary helpers for evidence pipeline artifacts.

Usage:
    from services.summarizer.stage_summary import (
        summarize_fetch_result,
        summarize_llm_context,
        summarize_evidence_result,
        build_stage_diagnostics,
    )
"""

from __future__ import annotations

from typing import Any

from services.fetch.schemas import FetchResult
from services.summarizer.models import EvidenceRequest, EvidenceResult


def summarize_fetch_result(fetch_result: FetchResult) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for post in fetch_result.posts:
        summary.append(
            {
                "post_id": post.id,
                "subreddit": post.subreddit,
                "title": post.title,
                "url": post.url,
                "relevance_score": post.relevance_score,
                "post_karma": post.post_karma,
                "matched_keywords": list(post.matched_keywords or []),
                "num_comments": len(post.comments or []),
            }
        )
    return summary


def summarize_llm_context(request: EvidenceRequest) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for payload in request.post_payloads:
        summary.append(
            {
                "post_id": payload.post_id,
                "subreddit": payload.subreddit,
                "title": payload.title,
                "url": payload.url,
                "relevance_score": payload.relevance_score,
                "post_karma": payload.post_karma,
                "matched_keywords": list(payload.matched_keywords or []),
                "num_comments": payload.num_comments,
            }
        )
    return summary


def summarize_evidence_result(result: EvidenceResult) -> dict[str, Any]:
    threads = [
        {
            "rank": thread.rank,
            "post_id": thread.post_id,
            "title": thread.title,
            "subreddit": thread.subreddit,
            "url": thread.url,
            "relevance_score": thread.relevance_score,
        }
        for thread in result.threads
    ]
    return {
        "status": result.status,
        "limitations": list(result.limitations),
        "threads": threads,
        "evidence_selected_post_ids": [thread.post_id for thread in result.threads],
    }


def build_stage_diagnostics(
    fetch_summary: list[dict[str, Any]],
    context_summary: list[dict[str, Any]],
    evidence_summary: dict[str, Any],
) -> dict[str, Any]:
    fetch_candidate_post_ids = {item["post_id"] for item in fetch_summary}
    llm_context_post_ids = {item["post_id"] for item in context_summary}
    llm_evidence_post_ids = set(evidence_summary.get("evidence_selected_post_ids") or [])
    return {
        "fetch_candidate_post_ids": sorted(fetch_candidate_post_ids),
        "llm_context_post_ids": sorted(llm_context_post_ids),
        "llm_evidence_post_ids": sorted(llm_evidence_post_ids),
        "dropped_before_context_post_ids": sorted(fetch_candidate_post_ids - llm_context_post_ids),
        "in_context_not_in_evidence_post_ids": sorted(llm_context_post_ids - llm_evidence_post_ids),
    }
