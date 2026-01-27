"""Generate middle-range pipeline stage summary artifacts.

Usage:
    python scripts/run_stage_summary.py --config config/run_config.yaml
    python scripts/run_stage_summary.py --config config/run_config.yaml --label scnA
"""
# Run: python scripts/run_stage_summary.py --config config/run_config.yaml

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
import yaml

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import get_logger
from demo.pipeline import _run_pipeline
from services.summarizer.stage_summary import (
    build_stage_diagnostics,
    summarize_evidence_result,
    summarize_fetch_result,
    summarize_llm_context,
)

logger = get_logger(__name__)
app = typer.Typer(add_completion=False)


def _sanitize_label(label: str) -> str:
    cleaned = label.strip().replace(" ", "-")
    return "".join(ch for ch in cleaned if ch.isalnum() or ch in {"-", "_"}).strip("-_")


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


@app.callback(invoke_without_command=True)
def main(
    config: Path = typer.Option(..., "--config", help="Path to YAML config."),
    query: str | None = typer.Option(None, "--query", help="Optional single query override."),
    label: str | None = typer.Option(
        None,
        "--label",
        help="Optional run label appended to the output filename (e.g., scnA).",
    ),
) -> None:
    """Run stage-boundary summaries for one or more queries."""
    run_start = time.perf_counter()
    cfg = _load_config(config)
    queries = _resolve_queries(cfg, query)

    output_dir = Path("data/pipeline_stage_summaries")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    output_label = _sanitize_label(label) if label else ""
    label_suffix = f"_{output_label}" if output_label else ""
    output_name = f"pipeline_stage_summary_{timestamp}{label_suffix}.json"
    output_path = output_dir / output_name

    payload: list[dict[str, Any]] = []
    for query_text in queries:
        plan, fetch_result, request, result = _run_pipeline(query_text, config)
        fetch_result_summary = summarize_fetch_result(fetch_result)
        llm_context_summary = summarize_llm_context(request)
        evidence_result_summary = summarize_evidence_result(result)
        diagnostics = build_stage_diagnostics(
            fetch_result_summary,
            llm_context_summary,
            evidence_result_summary,
        )
        record = {
            "query": query_text,
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
        payload.append(record)

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Pipeline stage summary saved to %s", output_path)
    logger.info(
        "Pipeline stage summary finished (queries=%d, total_s=%.2f).",
        len(queries),
        time.perf_counter() - run_start,
    )


if __name__ == "__main__":
    app()
