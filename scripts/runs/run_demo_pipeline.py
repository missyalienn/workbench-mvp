"""Run the demo evidence pipeline with a single query.

Usage:
    python scripts/runs/run_demo_pipeline.py
    python scripts/runs/run_demo_pipeline.py "my floor squeaks when I walk on it"
"""
# Run: python scripts/runs/run_demo_pipeline.py "my floor squeaks when I walk on it"

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import configure_logging, get_logger
from api.pipeline import run_evidence_pipeline

configure_logging()
logger = get_logger(__name__)
DEFAULT_QUERY = "my floor squeaks when I walk on it"


OUTPUT_DIR = Path("data/demo_runs")


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    payload = run_evidence_pipeline(query)

    artifact = {
        "query": query,
        "search_plan": payload["search_plan"],
        "evidence_result": payload["evidence_result"].model_dump(mode="json"),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"demo_run_{timestamp}.json"
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    logger.info("demo.complete", output_path=str(output_path))


if __name__ == "__main__":
    main()
