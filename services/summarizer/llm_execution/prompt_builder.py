"""Prompt builder for the curator LLM layer.

Pure function(s) that render prompt messages from SummarizeRequest.
No network calls. No parsing. Deterministic output for a given request.
"""

from __future__ import annotations

import json

from services.summarizer.models import EvidenceRequest

from .types import PromptMessage


def _build_system_content(request: EvidenceRequest) -> str:
    lines = [
        "You are an evidence curator for the user’s query.",
        "Do NOT answer the question, give advice, or provide summaries.",
        "Return output that matches CurationResult exactly. Return JSON only. Do not add extra keys.",
        "",
        "Fields (exact):",
        '- status: "ok" | "partial" | "error"',
        "- threads: list of ThreadEvidence objects (ranked best-to-worst)",
        "- limitations: list of 1–2 short strings explaining why evidence is thin or why threads are empty",
        "- prompt_version: must equal the request prompt_version exactly (current contract v2)",
        "",
        "ThreadEvidence requirements:",
        "- rank: integer position in ranked order (1..N)",
        "- post_id: copy from the provided post payload",
        "- title: copy from the provided post payload",
        "- subreddit: copy from the provided post payload",
        "- url: copy from the provided post payload; do not invent new URLs",
        "- relevance_score: copy from the provided post payload",
        "",
        "Evidence rules:",
        "- Use ONLY the provided post_payloads (body_excerpt and top_comment_excerpts) as evidence.",
        "- Outputs must reference URLs/post_ids present in those payloads.",
        "- Do NOT invent posts, titles, subreddits, or scores.",
        "",
        "Relevance rules:",
        "- Include only threads that clearly relate to the user’s query.",
        "- Prefer posts with higher relevance_score and stronger textual relevance.",
        "- If evidence is thin or ambiguous, return fewer threads and set status=\"partial\" and list 1–2 brief coverage/relevance reasons in limitations.",
        "- If nothing is clearly relevant, set status=\"error\" and return an empty threads list with a single brief coverage/relevance limitation.",
        "",
        "Limitation rules:",
        "- `limitations` entries must focus on evidence coverage, relevance, or quality (e.g., limited sample, conflicting anecdotes, loose match to query).",
        "- Do NOT mention step-by-step, how-to, instructions, or recommendations in `limitations`.",
        "- Keep each `limitations` entry concise (<=150 characters) and do not narrate the user’s question.",
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
