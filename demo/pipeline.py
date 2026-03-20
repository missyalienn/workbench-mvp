"""Demo evidence pipeline wrapper.

Usage:
    from demo.pipeline import run_evidence_pipeline
    result = run_evidence_pipeline("how to caulk bathtub")
"""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any, NamedTuple

import yaml

from agent.clients.openai_client import get_openai_client
from agent.planner.core import create_search_plan
from config.logging_config import get_logger
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.observability.run_context import elapsed_ms, generate_run_id, sanitize_query
from services.summarizer.config import EvidenceOutputConfig
from services.summarizer.llm_execution.llm_client import OpenAILLMClient
from services.summarizer.llm_execution.prompt_builder import build_messages
from services.summarizer.llm_execution.types import PromptMessage
from services.summarizer.models import EvidenceRequest, EvidenceResult
from services.summarizer.stage_summary import (
    build_stage_diagnostics,
    summarize_evidence_result,
    summarize_fetch_result,
    summarize_llm_context,
)
from services.summarizer.selector import build_summarize_request
from services.selector.config import SelectorConfig

logger = get_logger(__name__)
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "run_config.yaml"


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

class _PipelineRun(NamedTuple):
    plan: Any
    fetch_result: Any
    request: EvidenceRequest
    result: EvidenceResult


def _run_pipeline(
    query: str,
    config_path: Path | None,
    run_id: str | None = None,
) -> _PipelineRun:
    run_id = run_id or generate_run_id()
    safe_query = sanitize_query(query)
    pipeline_start = time.perf_counter()
    cfg = _load_config(config_path or DEFAULT_CONFIG_PATH)
    selector_cfg = _build_selector_config(cfg)
    curator_cfg = _build_curator_config(cfg)
    openai_env = cfg.get("openai_environment", "openai-dev")
    model = cfg.get("model", "gpt-4.1-mini")
    post_limit = cfg.get("post_limit", 10)
    prompt_version = cfg.get("prompt_version", "v3")
    allow_llm = cfg.get("allow_llm", False)
    if not allow_llm:
        raise RuntimeError("LLM calls disabled (allow_llm=false).")

    logger.info(
        "stage=pipeline_start event=start run_id=%s status=ok query=%s model=%s prompt_version=%s",
        run_id,
        safe_query,
        model,
        prompt_version,
    )

    planner_start = time.perf_counter()
    logger.info(
        "stage=planner_start event=start run_id=%s status=ok query=%s",
        run_id,
        safe_query,
    )
    plan = create_search_plan(query)
    logger.info(
        "stage=planner_end event=end run_id=%s status=ok duration_ms=%d plan_id=%s num_terms=%d num_subreddits=%d",
        run_id,
        elapsed_ms(planner_start),
        plan.plan_id,
        len(plan.search_terms),
        len(plan.subreddits),
    )

    fetch_start = time.perf_counter()
    logger.info(
        "stage=fetch_start event=start run_id=%s status=ok plan_id=%s tasks=%d post_limit=%d",
        run_id,
        plan.plan_id,
        len(plan.subreddits) * len(plan.search_terms),
        post_limit,
    )
    fetch_result = run_reddit_fetcher(
        plan=plan,
        post_limit=post_limit,
        run_id=run_id,
    )
    logger.info(
        "stage=fetch_end event=end run_id=%s status=ok duration_ms=%d plan_id=%s accepted_posts=%d",
        run_id,
        elapsed_ms(fetch_start),
        plan.plan_id,
        len(fetch_result.posts),
    )

    context_start = time.perf_counter()
    logger.info(
        "stage=context_start event=start run_id=%s status=ok plan_id=%s total_posts=%d",
        run_id,
        plan.plan_id,
        len(fetch_result.posts),
    )
    request = _build_request(
        fetch_result,
        selector_cfg,
        curator_cfg,
        prompt_version,
    )
    messages = _build_messages(request)
    logger.info(
        "stage=context_end event=end run_id=%s status=ok duration_ms=%d plan_id=%s selected_posts=%d total_posts=%d",
        run_id,
        elapsed_ms(context_start),
        plan.plan_id,
        len(request.post_payloads),
        len(fetch_result.posts),
    )

    client = get_openai_client(environment=openai_env)
    llm_client = OpenAILLMClient(client=client, model=model)
    llm_start = time.perf_counter()
    logger.info(
        "stage=llm_start event=start run_id=%s status=ok plan_id=%s model=%s prompt_version=%s",
        run_id,
        plan.plan_id,
        model,
        prompt_version,
    )
    result = _summarize(llm_client, messages)
    logger.info(
        "stage=llm_end event=end run_id=%s status=ok duration_ms=%d plan_id=%s model=%s prompt_version=%s",
        run_id,
        elapsed_ms(llm_start),
        plan.plan_id,
        model,
        prompt_version,
    )

    logger.info(
        "stage=pipeline_end event=end run_id=%s status=ok duration_ms=%d plan_id=%s threads=%d limitations_count=%d",
        run_id,
        elapsed_ms(pipeline_start),
        plan.plan_id,
        len(result.threads),
        len(result.limitations),
    )

    return _PipelineRun(
        plan=plan,
        fetch_result=fetch_result,
        request=request,
        result=result,
    )

 


def run_evidence_pipeline(
    query: str,
    *,
    config_path: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run the evidence pipeline for a single query and return evidence + plan info."""
    plan, _, _, result = _run_pipeline(query, config_path, run_id)
    return {
        "search_plan": {
            "search_terms": plan.search_terms,
            "subreddits": plan.subreddits,
            "notes": plan.notes,
        },
        "evidence_result": result,
    }


def pipeline_stage_summary(
    query: str,
    *,
    config_path: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run the evidence pipeline and return stage-boundary summaries only."""
    plan, fetch_result, request, result = _run_pipeline(query, config_path, run_id)
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
            "notes": plan.notes,
        },
        "fetch_result_summary": fetch_result_summary,
        "llm_context_summary": llm_context_summary,
        "evidence_result_summary": evidence_result_summary,
        "diagnostics": diagnostics,
    }
