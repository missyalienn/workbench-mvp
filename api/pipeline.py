"""Evidence pipeline orchestrator.

Usage:
    from api.pipeline import run_evidence_pipeline
    result = await run_evidence_pipeline("how to caulk bathtub")
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any, NamedTuple

import yaml

from agent.clients.openai_client import get_openai_client
from agent.planner.core import create_search_plan
from config.logging_config import get_logger, plan_context_scope
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.synthesizer.config import EvidenceOutputConfig
from services.synthesizer.llm_execution.llm_client import OpenAILLMClient
from services.synthesizer.llm_execution.prompt_builder import build_messages
from services.synthesizer.llm_execution.types import PromptMessage
from services.synthesizer.models import EvidenceRequest, EvidenceResult
from services.synthesizer.stage_summary import (
    build_stage_diagnostics,
    summarize_evidence_result,
    summarize_fetch_result,
    summarize_llm_context,
)
from services.synthesizer.context_builder import build_context_request
from services.context_builder.config import ContextBuilderConfig

logger = get_logger(__name__)
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "run_config.yaml"


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _build_context_builder_config(cfg: dict[str, Any]) -> ContextBuilderConfig:
    return ContextBuilderConfig(
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
    selector_cfg: ContextBuilderConfig,
    curator_cfg: EvidenceOutputConfig,
    prompt_version: str,
) -> EvidenceRequest:
    return build_context_request(
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

class _PipelineRun(NamedTuple):
    plan: Any
    fetch_result: Any
    request: EvidenceRequest
    result: EvidenceResult


async def _run_pipeline(
    query: str,
    config_path: Path | None,
) -> _PipelineRun:
    cfg = _load_config(config_path or DEFAULT_CONFIG_PATH)
    selector_cfg = _build_context_builder_config(cfg)
    curator_cfg = _build_curator_config(cfg)
    openai_env = cfg.get("openai_environment", "openai-dev")
    planner_model = cfg.get("planner_model", "gpt-4.1-mini")
    summarizer_model = cfg.get("summarizer_model", "gpt-4.1-mini")
    post_limit = cfg.get("post_limit", 10)
    prompt_version = cfg.get("prompt_version", "v3")
    t0 = time.monotonic()
    logger.info(
        "pipeline.start",
        planner_model=planner_model,
        summarizer_model=summarizer_model,
        prompt_version=prompt_version,
    )

    plan = await asyncio.to_thread(create_search_plan, query, model=planner_model)

    with plan_context_scope(str(plan.plan_id)):
        fetch_result = await run_reddit_fetcher(plan=plan, post_limit=post_limit)
        request = _build_request(fetch_result, selector_cfg, curator_cfg, prompt_version)
        messages = _build_messages(request)

        client = get_openai_client(environment=openai_env)
        llm_client = OpenAILLMClient(client=client, model=summarizer_model)
        result = await asyncio.to_thread(llm_client.summarize_structured, messages=messages)

        logger.info(
            "pipeline.complete",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
            status=result.status,
            n_threads=len(result.threads) if result.threads else 0,
        )

        return _PipelineRun(
            plan=plan,
            fetch_result=fetch_result,
            request=request,
            result=result,
        )

 


async def run_evidence_pipeline(
    query: str,
    *,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Run the evidence pipeline for a single query and return evidence + plan info."""
    plan, _, _, result = await _run_pipeline(query, config_path)
    return {
        "search_plan": {
            "search_terms": plan.search_terms,
            "subreddits": plan.subreddits,
        },
        "evidence_result": result,
    }


async def pipeline_stage_summary(
    query: str,
    *,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Run the evidence pipeline and return stage-boundary summaries only."""
    plan, fetch_result, request, result = await _run_pipeline(query, config_path)
    fetch_result_summary = summarize_fetch_result(fetch_result)
    llm_context_summary = summarize_llm_context(request)
    evidence_result_summary = summarize_evidence_result(result)
    diagnostics = build_stage_diagnostics(
        fetch_result_summary,
        llm_context_summary,
        evidence_result_summary,
    )

    return {
        "search_plan": {
            "search_terms": plan.search_terms,
            "subreddits": plan.subreddits,
        },
        "fetch_result_summary": fetch_result_summary,
        "llm_context_summary": llm_context_summary,
        "evidence_result_summary": evidence_result_summary,
        "diagnostics": diagnostics,
    }
