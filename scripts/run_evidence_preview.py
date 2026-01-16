"""Preview harness for the evidence pipeline."""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
import yaml

from agent.clients.openai_client import get_openai_client
from agent.planner.core import create_search_plan
from config.logging_config import get_logger
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.summarizer.config import EvidenceOutputConfig
from services.summarizer.llm_execution.errors import (
    LLMStructuredOutputError,
    LLMTransportError,
)
from services.summarizer.llm_execution.llm_client import OpenAILLMClient
from services.summarizer.llm_execution.prompt_builder import build_messages
from services.summarizer.llm_execution.types import PromptMessage
from services.summarizer.models import EvidenceRequest, EvidenceResult
from services.summarizer.selector import build_summarize_request
from services.selector.config import SelectorConfig

logger = get_logger(__name__)
app = typer.Typer(add_completion=False)


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise typer.BadParameter(f"Config not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _resolve_queries(cfg: dict[str, Any], query_override: str | None) -> list[str]:
    if query_override:
        return [query_override]
    queries = cfg.get("queries")
    if not queries:
        raise typer.BadParameter("Config must include non-empty 'queries'.")
    return list(queries)


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
    """Build the SummarizeRequest from a FetchResult."""
    return build_summarize_request(
        fetch_result,
        selector_cfg,
        prompt_version,
        curator_cfg,
    )


def _build_messages(request: EvidenceRequest) -> list[PromptMessage]:
    """Build prompt messages for a EvidenceRequest."""
    return build_messages(request)


def _summarize(
    llm_client: OpenAILLMClient,
    messages: list[PromptMessage],
) -> EvidenceResult:
    return llm_client.summarize_structured(messages=messages)


def _preview_counts(request: EvidenceRequest) -> dict[str, int]:
    total_comments = sum(len(post.top_comment_excerpts) for post in request.post_payloads)
    return {
        "num_posts": len(request.post_payloads),
        "num_comments": total_comments,
    }


@app.command()
def run(
    config: Path = typer.Option(..., "--config", help="Path to YAML config."),
    query: str | None = typer.Option(None, "--query", help="Optional single query override."),
    mode: str = typer.Option(
        "fixture_and_llm",
        "--mode",
        help="Mode to run: fixture_only or fixture_and_llm.",
    ),
) -> None:
    """Run the evidence preview for one or more queries."""
    cfg = _load_config(config)

    logger.info("Loaded evidence preview config from %s", config)

    queries = _resolve_queries(cfg, query)
    selector_cfg = _build_selector_config(cfg)
    curator_cfg = _build_curator_config(cfg)
    openai_env = cfg.get("openai_environment", "openai-dev")
    model = cfg.get("model", "gpt-4.1-mini")
    post_limit = cfg.get("post_limit", 10)
    prompt_version = cfg.get("prompt_version", "v1")
    allow_llm = cfg.get("allow_llm", False)
    if mode != "fixture_only" and not allow_llm:
        logger.warning(
            "LLM calls disabled (allow_llm=false); forcing fixture_only mode."
        )
        mode = "fixture_only"

    client = get_openai_client(environment=openai_env)
    llm_client = OpenAILLMClient(client=client, model=model)

    logger.info(
        "Curator smoke test starting (queries=%d, model=%s, prompt_version=%s).",
        len(queries),
        model,
        prompt_version,
    )
    logger.debug("CLI overrides: query=%s, mode=%s", query, mode)

    preview_payload: list[dict[str, Any]] = []
    llm_error_occurred = False
    output_dir = Path("data/evidence_previews")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_name = cfg.get("output_filename") or f"evidence_preview_{timestamp}.json"
    output_path = output_dir / output_name

    for query_text in queries:
        total_start = time.perf_counter()
        record: dict[str, Any] = {"query": query_text}
        plan = None

        try:
            planner_start = time.perf_counter()
            plan = create_search_plan(query_text)
            planner_ms = int((time.perf_counter() - planner_start) * 1000)
            logger.info(
                "SearchPlan created [plan_id=%s, query=%r, search_terms=%s, subreddits=%s, notes=%r]",
                plan.plan_id,
                plan.query,
                plan.search_terms,
                plan.subreddits,
                plan.notes[:300] if plan.notes else "",
            )
            record["plan"] = {
                "plan_id": str(plan.plan_id),
                "search_terms": plan.search_terms,
                "subreddits": plan.subreddits,
                "reasoning": plan.notes,
            }

        except Exception as exc:
            record.update(
                {
                    "status": "planner_failed",
                    "error": {"exc_type": type(exc).__name__, "message": str(exc)},
                }
            )
            preview_payload.append(record)
            continue

        try:
            fetch_start = time.perf_counter()
            fetch_result = run_reddit_fetcher(
                plan=plan,
                post_limit=post_limit,
            )
            fetch_ms = int((time.perf_counter() - fetch_start) * 1000)
            top3 = sorted(fetch_result.posts, key=lambda p: p.relevance_score, reverse=True)[:3]
            logger.info(
                "Fetch summary [plan_id=%s, num_posts=%d, top3=%s]",
                fetch_result.plan_id,
                len(fetch_result.posts),
                [(p.id, p.relevance_score) for p in top3],
            )

        except Exception as exc:
            record.update(
                {
                    "plan_id": str(plan.plan_id),
                    "status": "fetch_failed",
                    "error": {"exc_type": type(exc).__name__, "message": str(exc)},
                }
            )
            preview_payload.append(record)
            continue

        request = _build_request(
            fetch_result,
            selector_cfg,
            curator_cfg,
            prompt_version,
        )
        top_payload = request.post_payloads[0] if request.post_payloads else None
        second_payload = request.post_payloads[1] if len(request.post_payloads) > 1 else None
        logger.info(
            "LLM payload preview [plan_id=%s, num_posts=%d, top_post=%s, top_score=%s, second_post=%s, second_score=%s]",
            plan.plan_id,
            len(request.post_payloads),
            top_payload.post_id if top_payload else None,
            top_payload.relevance_score if top_payload else None,
            second_payload.post_id if second_payload else None,
            second_payload.relevance_score if second_payload else None,
        )
        counts = _preview_counts(request)

        record.update(
            {
                "plan_id": str(plan.plan_id),
                "status": "ok_fixture_only" if mode == "fixture_only" else "ok",
                    "meta": {
                        "model": model,
                        "prompt_version": prompt_version,
                        "openai_environment": openai_env,
                        "post_limit": post_limit,
                    **counts,
                    "timing_ms": {
                        "planner_ms": planner_ms,
                        "fetch_ms": fetch_ms,
                    },
                },
            }
        )

        if mode == "fixture_only":
            record["meta"]["timing_ms"]["total_ms"] = int(
                (time.perf_counter() - total_start) * 1000
            )
            preview_payload.append(record)
            continue
        try:
            llm_start = time.perf_counter()
            messages = _build_messages(request)
            result = _summarize(llm_client, messages)
            logger.info(
                "OpenAI Responses API returned EvidenceResult (model=%s, prompt_version=%s, query=%s)",
                model,
                prompt_version,
                query_text,
            )
            llm_ms = int((time.perf_counter() - llm_start) * 1000)
            record["curation_result"] = result.model_dump(mode="json")
            record["meta"]["timing_ms"]["llm_ms"] = llm_ms
        except LLMStructuredOutputError as exc:
            logger.error(
                "LLM structured output error (plan_id=%s, query=%s): %s details=%s cause=%s",
                plan.plan_id if plan else None,
                query_text,
                str(exc),
                exc.details,
                repr(exc.cause) if exc.cause else None,
            )
            llm_error_occurred = True
            record.update(
                {
                    "status": "parse_failed",
                    "error": {
                        "exc_type": type(exc).__name__,
                        "message": str(exc),
                        "details": exc.details,
                        "cause": repr(exc.cause) if exc.cause else None,
                    },
                }
            )
        except LLMTransportError as exc:
            logger.error(
                "LLM transport error (plan_id=%s, query=%s): %s details=%s cause=%s",
                plan.plan_id if plan else None,
                query_text,
                str(exc),
                exc.details,
                repr(exc.cause) if exc.cause else None,
            )
            llm_error_occurred = True
            record.update(
                {
                    "status": "llm_failed",
                    "error": {
                        "exc_type": type(exc).__name__,
                        "message": str(exc),
                        "details": exc.details,
                        "cause": repr(exc.cause) if exc.cause else None,
                    },
                }
            )
        finally:
            record["meta"]["timing_ms"]["total_ms"] = int(
                (time.perf_counter() - total_start) * 1000
            )
            preview_payload.append(record)

    if llm_error_occurred:
        logger.error(
            "LLM errors occurred; skipping preview write for %s",
            output_path,
        )
        return

    output_path.write_text(json.dumps(preview_payload, indent=2), encoding="utf-8")
    logger.info("Evidence preview saved to data/evidence_previews/%s", output_name)


if __name__ == "__main__":
    if __package__ is None or __package__ == "":
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
    app()
