"""Prompt builder for the summarizer LLM layer.

Pure function(s) that render prompt messages from SummarizeRequest.
No network calls. No parsing. Deterministic output for a given request.
"""

from __future__ import annotations

import json

from services.summarizer.models import SummarizeRequest

from .types import PromptMessage


def _build_system_content(request: SummarizeRequest) -> str:
    lines = [
        "You summarize Reddit posts/comments to answer the user's query.",
        "Return output that matches SummarizeResult exactly. Return JSON only. Do not add extra keys.",
        "Fields:",
        'status: "ok" | "partial" | "error"',
        "summary: string",
        f"highlights: list of strings (max {request.max_highlights})",
        f"cautions: list of strings (max {request.max_cautions})",
        "sources: list of objects with string keys and string values",
        "prompt_version: must equal the request prompt_version",
        "Grounding rules:",
        "Use only provided url values; do not invent sources or URLs.",
        'If evidence conflicts or is weak, set status="partial" and explain in cautions.',
        'If evidence is not relevant, set status="error" and explain in summary; keep lists minimal.',
        "Caps:",
        f"summary must be <= {request.summary_char_budget} characters",
    ]
    return "\n".join(lines)


def _build_user_content(request: SummarizeRequest) -> str:
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


def build_messages(request: SummarizeRequest) -> list[PromptMessage]:
    """Build system + user messages for the summarizer LLM."""
    return [
        PromptMessage(role="system", content=_build_system_content(request)),
        PromptMessage(role="user", content=_build_user_content(request)),
    ]
