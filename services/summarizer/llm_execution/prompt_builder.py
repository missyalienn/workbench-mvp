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
        "",
        "Return output that matches SummarizeResult exactly. Return JSON only. Do not add extra keys.",
        "",
        "Fields (exact):",
        '- status: "ok" | "partial" | "error"',
        f"- summary: string (<= {request.summary_char_budget} characters)",
        f"- highlights: list of strings (max {request.max_highlights})",
        f"- cautions: list of strings (max {request.max_cautions})",
        "- sources: list of objects with keys: url, post_id, subreddit, title, excerpt, supports",
        "- prompt_version: must equal the request prompt_version exactly",
        "",
        "Evidence selection rules (do NOT output your selection; use it internally):",
        "- Before writing, decide which provided post_payloads are relevant to the query.",
        "- Evidence is ONLY the provided body_excerpt and top_comment_excerpts from the provided payloads.",
        "- Do NOT use general knowledge, “common sense”, or unstated assumptions. If something is not in the evidence, you must not claim it.",
        "",
        "Synthesis rules:",
        "- Write summary, highlights, and cautions using ONLY the selected evidence.",
        "- Do NOT introduce tools, materials, steps, measurements, safety instructions, or claims that do not appear in the evidence text.",
        "- Prefer fewer, higher-confidence claims over broad coverage.",
        '- If evidence is weak, incomplete, or conflicting, set status="partial" and explain why in cautions.',
        '- If evidence is not relevant to the query, set status="error" and explain briefly in summary; keep lists minimal.',
        "",
        "Source rules (grounding):",
        "- You may ONLY cite URLs that appear in the provided post_payloads (no new URLs).",
        "- Every highlight must be supported by at least one source entry.",
        "- Each source object must include these keys (all values must be strings):",
        "  - url: the cited post URL from the provided payloads",
        "  - post_id: the cited post ID from the provided payloads",
        "  - subreddit: the cited subreddit from the provided payloads",
        "  - title: the cited post title from the provided payloads",
        "  - excerpt: a short snippet copied verbatim from body_excerpt or a top_comment_excerpts entry",
        "  - supports: the highlight text (or a clearly identifying substring) that this source supports",
        "- The excerpt must be an exact quote from the evidence (no paraphrase) and should make the support obvious.",
        "",
        "Caps:",
        f"- summary must be <= {request.summary_char_budget} characters.",
        f"- highlights length <= {request.max_highlights}; cautions length <= {request.max_cautions}.",
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
