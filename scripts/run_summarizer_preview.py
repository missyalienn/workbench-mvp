"""Smoke-test harness for the summarizer pipeline."""

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
from services.summarizer.config import SummarizerConfig
from services.summarizer.llm_execution.errors import (
    LLMStructuredOutputError,
    LLMTransportError,
)
from services.summarizer.llm_execution.llm_client import OpenAILLMClient
from services.summarizer.llm_execution.prompt_builder import build_messages
from services.summarizer.llm_execution.types import PromptMessage
from services.summarizer.models import SummarizeRequest, SummarizeResult
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


def _build_summarizer_config(cfg: dict[str, Any]) -> SummarizerConfig:
    return SummarizerConfig(
        summary_char_budget=cfg["summary_char_budget"],
        max_highlights=cfg["max_highlights"],
        max_cautions=cfg["max_cautions"],
    )


def _build_request(
    fetch_result: Any,
    selector_cfg: SelectorConfig,
    summarizer_cfg: SummarizerConfig,
    prompt_version: str,
) -> SummarizeRequest:
    """Build the SummarizeRequest from a FetchResult."""
    return build_summarize_request(
        fetch_result,
        selector_cfg,
        prompt_version,
        summarizer_cfg,
    )


def _build_messages(request: SummarizeRequest) -> list[PromptMessage]:
    """Build prompt messages for a SummarizeRequest."""
    return build_messages(request)


def _summarize(
    llm_client: OpenAILLMClient,
    messages: list[PromptMessage],
) -> SummarizeResult:
    return llm_client.summarize_structured(messages=messages)


def _preview_counts(request: SummarizeRequest) -> dict[str, int]:
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
    """Run the summarizer smoke test for one or more queries."""
    cfg = _load_config(config)

    logger.info("Loaded summarizer smoke-test config from %s", config)

    queries = _resolve_queries(cfg, query)
    selector_cfg = _build_selector_config(cfg)
    summarizer_cfg = _build_summarizer_config(cfg)
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
        "Summarizer smoke test starting (queries=%d, model=%s, prompt_version=%s).",
        len(queries),
        model,
        prompt_version,
    )
    logger.debug("CLI overrides: query=%s, mode=%s", query, mode)

    preview_payload: list[dict[str, Any]] = []
    llm_error_occurred = False
    output_dir = Path("data/summarizer_previews")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_name = cfg.get("output_filename") or f"summarizer_preview_{timestamp}.json"
    output_path = output_dir / output_name

    for query_text in queries:
        total_start = time.perf_counter()
        record: dict[str, Any] = {"query": query_text}
        plan = None

        try:
            planner_start = time.perf_counter()
            plan = create_search_plan(query_text)
            planner_ms = int((time.perf_counter() - planner_start) * 1000)
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
                environment="dev",
            )
            fetch_ms = int((time.perf_counter() - fetch_start) * 1000)
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
            summarizer_cfg,
            prompt_version,
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
            llm_ms = int((time.perf_counter() - llm_start) * 1000)
            record["summarize_result"] = result.model_dump(mode="json")
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
    logger.info("Summarizer preview saved to %s", output_path)


if __name__ == "__main__":
    if __package__ is None or __package__ == "":
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
    app()
