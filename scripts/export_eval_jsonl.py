"""Export evidence preview JSON into JSONL eval records.

Usage:
    python scripts/export_eval_jsonl.py data/evidence_previews/evidence_preview_20260116_020157.json
    python scripts/export_eval_jsonl.py data/evidence_previews/evidence_preview_20260116_020157.json data/evidence_previews/evidence_preview_20260116_020157.jsonl
"""
# Run: python scripts/export_eval_jsonl.py data/evidence_previews/evidence_preview_20260116_020157.json

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import get_logger

logger = get_logger(__name__)


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Preview JSON not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Preview JSON must be a list of records.")
    return payload


def _build_eval_record(record: dict[str, Any], index: int) -> dict[str, Any]:
    plan = record.get("plan") or {}
    plan_id = record.get("plan_id") or plan.get("plan_id") or f"record_{index}"
    meta = dict(record.get("meta") or {})
    status = record.get("status")
    if status:
        meta["status"] = status
    error = record.get("error")
    if error:
        meta["error"] = error

    return {
        "id": plan_id,
        "query": record.get("query"),
        "input": {
            "plan": plan if plan else None,
            "evidence_request": record.get("evidence_request"),
        },
        "output": {
            "curation_result": record.get("curation_result"),
        },
        "retrieval": {
            "fetch_result_summary": record.get("fetch_result_summary"),
        },
        "metadata": meta,
    }


def _write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    lines = [
        json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        for record in records
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/export_eval_jsonl.py INPUT_JSON [OUTPUT_JSONL]")
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".jsonl")

    raw_records = _load_records(input_path)
    eval_records = [
        _build_eval_record(record, index)
        for index, record in enumerate(raw_records, start=1)
    ]
    _write_jsonl(eval_records, output_path)
    logger.info("Eval JSONL written to %s (%d records)", output_path, len(eval_records))


if __name__ == "__main__":
    main()
