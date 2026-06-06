"""Prompt builder for the curator LLM layer.

Pure function(s) that render prompt messages from EvidenceRequest.
No network calls. No parsing. Deterministic output for a given request.
"""

from __future__ import annotations

import json

from services.synthesizer.models import EvidenceRequest

from .types import PromptMessage


def _build_system_content_v3(request: EvidenceRequest) -> str:
    lines = [
        "You are a research synthesizer for the user's query.",
        "Return only JSON matching EvidenceResult schema. No extra keys.",
        "",
        "Fields:",
        '- status: "ok" | "partial" | "insufficient"',
        "- summary: 1-2 sentences synthesizing what the evidence says about the query. Focus on the most common or actionable findings across threads. If status is 'insufficient', briefly describe what was found (or not found).",
        "- limitations: 1-2 short strings explaining thin/empty evidence",
        "",
        "Evidence rules:",
        "- Use ONLY provided post_payloads (body_excerpt, top_comment_excerpts).",
        "- Do NOT invent findings beyond the provided evidence.",
        "",
        "Relevance rules:",
        "- Base the summary on the strongest and most relevant evidence in the provided posts.",
        "- Prefer higher relevance_score and stronger textual match when weighing the evidence.",
        "- Thin/ambiguous evidence: return status='partial' and add limitations.",
        "- No relevant evidence: return status='insufficient' and add a limitation.",
        "",
        "Limitations:",
        "- Describe only coverage gaps directly tied to the user's query: what scenarios, cases, or detail the evidence doesn't cover.",
        "- Never mention: 'step-by-step', 'instructions', 'how-to', 'advice', 'recommendations'.",
        "- Keep under 150 chars each.",
        "- Good: 'Most posts focus on one repair situation, so other cases get less attention.'",
        "- Bad: 'Limited installation instructions.' (mentions instructions)",
    ]
    return "\n".join(lines)


def _build_system_content_v4(request: EvidenceRequest) -> str:
    lines = [
        "You are a research synthesizer for the user's query.",
        "Return only JSON matching EvidenceResult schema. No extra keys.",
        "",
        "Fields:",
        '- status: "ok" | "partial" | "insufficient"',
        "- summary: 1-2 sentences synthesizing what the evidence says about the query. Focus on the most common or actionable findings across threads. If status is 'insufficient', briefly describe what was found (or not found).",
        "- limitations: 1-2 concise, bullet-ready strings explaining evidence caveats in natural, reader-friendly language.",
        "",
        "Evidence rules:",
        "- Use ONLY provided post_payloads (body_excerpt, top_comment_excerpts).",
        "- Do NOT invent findings beyond the provided evidence.",
        "",
        "Relevance rules:",
        "- Base the summary on the strongest and most relevant evidence in the provided posts.",
        "- Thin/ambiguous evidence: return status='partial' and add limitations.",
        "- No relevant evidence: return status='insufficient' and add a limitation.",
        "",
        "Limitations rules:",
        "- Describe only coverage gaps directly tied to the user's query: what scenarios, cases, or detail the evidence doesn't cover.",
        "- Keep each bullet short, plainspoken, and under 110 chars.",
        "",
        "Example output:",
        "{",
        '  "status": "partial",',
        '  "summary": "Most posts agree the fix is X, though results vary by situation.",',
        '  "limitations": [',
        '    "Posts focus on Y scenario; other cases get less coverage.",',
        '    "Some threads lack detail on Z, so edge cases are underrepresented."',
        "  ]",
        "}",
    ]
    return "\n".join(lines)


def _build_system_content(request: EvidenceRequest) -> str:
    builders = {
        "v3": _build_system_content_v3,
        "v4": _build_system_content_v4,
    }
    try:
        return builders[request.prompt_version](request)
    except KeyError as exc:
        raise ValueError(f"Unsupported prompt_version: {request.prompt_version}") from exc


def _build_user_content(request: EvidenceRequest) -> str:
    _EXCLUDE_FROM_PAYLOAD = {"matched_keywords"}
    payload = {
        "query": request.query,
        "prompt_version": request.prompt_version,
        # Ensure JSON-safe values (e.g., HttpUrl -> str).
        "post_payloads": [
            post.model_dump(mode="json", exclude=_EXCLUDE_FROM_PAYLOAD)
            for post in request.post_payloads
        ],
    }

    # Compact JSON to reduce tokens.
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_messages(request: EvidenceRequest) -> list[PromptMessage]:
    """Build system + user messages for the curator LLM."""
    return [
        PromptMessage(role="system", content=_build_system_content(request)),
        PromptMessage(role="user", content=_build_user_content(request)),
    ]
