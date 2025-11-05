"""
Baseline evaluation script for the Planner agent.

Run a fixed set of novice DIY queries against the planner, validate with SearchPlan,
and write outcomes to a timestamped JSONL file for quick regressions.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

if __package__ is None or __package__ == "":
    # Allow running as `python scripts/baseline_eval.py` by adding repo root.
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from agent.planner import SearchPlan, create_search_plan
from config.logging_config import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)

# Baseline queries cover common DIY questions a beginner might ask.
BASELINE_QUERIES: list[str] = [
    "How can I build a simple workbench for my garage?",
    "What's the safest way to replace a broken light switch?",
    "How do I choose the right sandpaper grit for refinishing a table?",
    "What steps do I take to install floating shelves on drywall?",
    "How do I fix a squeaky interior door?",
    "How can I seal gaps around my drafty windows?",
    "What's the best way to stain a pine bookshelf evenly?",
    "How do I patch a small hole in drywall without it showing?",
    "How can I sharpen my chisels with basic tools?",
    "What beginner tools do I need to start woodworking projects?",
]


def evaluate_query(query: str) -> dict[str, Any]:
    """
    Execute the planner for a single query and capture validation status.

    Returns:
        Dict with query, runtime, validity flag, and optional error or plan_id.
    """
    start = perf_counter()
    record: dict[str, Any] = {"query": query}

    try:
        raw_plan = create_search_plan(query)
        if isinstance(raw_plan, SearchPlan):
            plan = SearchPlan.model_validate(raw_plan.model_dump())
        else:
            plan = SearchPlan.model_validate(raw_plan)  # type: ignore[arg-type]
        record.update(
            runtime_seconds=round(perf_counter() - start, 4),
            valid=True,
            plan_id=str(plan.plan_id),
        )
    except ValidationError as exc:
        error_message = "; ".join(err["msg"] for err in exc.errors())
        record.update(
            runtime_seconds=round(perf_counter() - start, 4),
            valid=False,
            error=error_message,
        )
        logger.error("Validation failed for query '%s': %s", query, error_message)
    except Exception as exc:
        record.update(
            runtime_seconds=round(perf_counter() - start, 4),
            valid=False,
            error=str(exc),
        )
        logger.error("Planner raised error for query '%s': %s", query, exc)

    return record


def write_results(results: list[dict[str, Any]]) -> Path:
    """
    Persist evaluation records to JSONL so future runs can append or diff results.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path("logs") / f"baseline_eval_{timestamp}.jsonl"

    with output_path.open("w", encoding="utf-8") as jsonl_file:
        for record in results:
            jsonl_file.write(json.dumps(record, ensure_ascii=True))
            jsonl_file.write("\n")

    return output_path


def run_baseline(queries: list[str]) -> None:
    """
    Run the baseline suite and log an at-a-glance summary for developers.
    """
    logger.info("Running planner baseline with %d queries", len(queries))
    results = [evaluate_query(query) for query in queries]
    output_path = write_results(results)

    valid_count = sum(1 for record in results if record.get("valid"))
    total = len(results)
    logger.info(
        "Baseline complete: %d/%d valid outputs (results: %s)",
        valid_count,
        total,
        output_path,
    )


def main() -> None:
    """
    Entry point so the script can be invoked directly or imported for reuse.
    """
    run_baseline(BASELINE_QUERIES)


if __name__ == "__main__":
    main()
