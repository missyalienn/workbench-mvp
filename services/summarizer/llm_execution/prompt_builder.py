"""Prompt builder for the curator LLM layer.

Pure function(s) that render prompt messages from EvidenceRequest.
No network calls. No parsing. Deterministic output for a given request.
"""

from __future__ import annotations

import json

from services.summarizer.models import EvidenceRequest

from .types import PromptMessage


def _build_system_content(request: EvidenceRequest) -> str:
    lines = [
        "You are an evidence curator for the user's query.",
        "Return only JSON matching EvidenceResult schema. No summaries, advice, or extra keys.",
        "",
        "Fields:",
        '- status: "ok" | "partial" | "error"',
        "- threads: list of ThreadEvidence (ranked best-to-worst)",
        "- limitations: 1-2 short strings explaining thin/empty evidence",
        "- prompt_version: must match request prompt_version exactly (current: v3)",
        "",
        "ThreadEvidence: rank (1..N), copy post_id/title/subreddit/url/relevance_score exactly from payload.",
        "",
        "Evidence rules:",
        "- Use ONLY provided post_payloads (body_excerpt, top_comment_excerpts).",
        "- Do NOT invent posts, titles, subreddits, scores, or URLs.",
        "",
        "Relevance rules:",
        "- Include only threads clearly relating to user's query.",
        "- Prefer higher relevance_score and stronger textual match.",
        "- Thin/ambiguous evidence: return fewer threads, status='partial', add limitations.",
        "- No relevant evidence: status='error', empty threads list, add limitation.",
        "",
        "Limitations:",
        "- Describe gaps in EVIDENCE ONLY (thread count, coverage, quality).",
        "- Never mention: 'step-by-step', 'instructions', 'how-to', 'advice', 'recommendations'.",
        "- Keep under 150 chars each.",
        "- Good: 'Only 4 threads found; most discuss metal studs vs. standard drywall.'",
        "- Bad: 'Limited installation instructions.' (mentions instructions)",
    ]
    return "\n".join(lines)


def _build_user_content(request: EvidenceRequest) -> str:
    payload = {
        "query": request.query,
        "prompt_version": request.prompt_version,
        "constraints": {
            "summary_char_budget": int(request.summary_char_budget),
            "max_highlights": int(request.max_highlights),
            "max_cautions": int(request.max_cautions),
        },
        # Ensure JSON-safe values (e.g., HttpUrl -> str).
        "post_payloads": [post.model_dump(mode="json") for post in request.post_payloads],
    }

    # Compact JSON to reduce tokens.
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_messages(request: EvidenceRequest) -> list[PromptMessage]:
    """Build system + user messages for the curator LLM."""
    return [
        PromptMessage(role="system", content=_build_system_content(request)),
        PromptMessage(role="user", content=_build_user_content(request)),
    ]
