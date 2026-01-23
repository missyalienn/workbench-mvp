"""Demo evidence pipeline wrapper.

Usage:
    from demo.pipeline import run_evidence_pipeline
    result = run_evidence_pipeline("how to caulk bathtub")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent.clients.openai_client import get_openai_client
from agent.planner.core import create_search_plan
from config.logging_config import get_logger
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.summarizer.config import EvidenceOutputConfig
from services.summarizer.llm_execution.llm_client import OpenAILLMClient
from services.summarizer.llm_execution.prompt_builder import build_messages
from services.summarizer.llm_execution.types import PromptMessage
from services.summarizer.models import EvidenceRequest, EvidenceResult
from services.summarizer.selector import build_summarize_request
from services.selector.config import SelectorConfig

logger = get_logger(__name__)
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "evidence_preview.yaml"


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _build_selector_config(cfg: dict[str, Any]) -> SelectorConfig:
    return SelectorConfig(
        max_posts=cfg["max_posts"],
        max_comments_per_post=cfg["max_comments_per_post"],
        max_post_chars=cfg["max_post_chars"],
        max_comment_chars=cfg["max_comment_chars"],
    )


def _build_curator_config(cfg: dict[str, Any]) -> EvidenceOutputConfig:
    return EvidenceOutputConfig(
        summary_char_budget=cfg["summary_char_budget"],
        max_highlights=cfg["max_highlights"],
        max_cautions=cfg["max_cautions"],
    )


def _build_request(
    fetch_result: Any,
    selector_cfg: SelectorConfig,
    curator_cfg: EvidenceOutputConfig,
    prompt_version: str,
) -> EvidenceRequest:
    return build_summarize_request(
        fetch_result,
        selector_cfg,
        prompt_version,
        curator_cfg,
    )


def _build_messages(request: EvidenceRequest) -> list[PromptMessage]:
    return build_messages(request)


def _summarize(
    llm_client: OpenAILLMClient,
    messages: list[PromptMessage],
) -> EvidenceResult:
    return llm_client.summarize_structured(messages=messages)


def run_evidence_pipeline(
    query: str,
    *,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Run the evidence pipeline for a single query and return evidence + plan info."""
    cfg = _load_config(config_path or DEFAULT_CONFIG_PATH)
    selector_cfg = _build_selector_config(cfg)
    curator_cfg = _build_curator_config(cfg)
    openai_env = cfg.get("openai_environment", "openai-dev")
    model = cfg.get("model", "gpt-4.1-mini")
    post_limit = cfg.get("post_limit", 10)
    prompt_version = cfg.get("prompt_version", "v3")
    allow_llm = cfg.get("allow_llm", False)
    if not allow_llm:
        # TODO(mallan): define fixture-only or fallback behavior for allow_llm=false.
        raise RuntimeError("LLM calls disabled (allow_llm=false).")

    logger.info(
        "Evidence pipeline starting (model=%s, prompt_version=%s).",
        model,
        prompt_version,
    )

    plan = create_search_plan(query)
    fetch_result = run_reddit_fetcher(
        plan=plan,
        post_limit=post_limit,
    )
    request = _build_request(
        fetch_result,
        selector_cfg,
        curator_cfg,
        prompt_version,
    )
    messages = _build_messages(request)

    client = get_openai_client(environment=openai_env)
    llm_client = OpenAILLMClient(client=client, model=model)
    result = _summarize(llm_client, messages)
    return {
        "search_plan": {
            "search_terms": plan.search_terms,
            "subreddits": plan.subreddits,
            "notes": plan.notes,
        },
        "evidence_result": result,
    }
