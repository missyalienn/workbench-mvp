"""Run the demo evidence pipeline with a single query.

Usage:
    python scripts/run_demo_pipeline.py
    python scripts/run_demo_pipeline.py "my floor squeaks when I walk on it"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import get_logger
from demo.pipeline import run_evidence_pipeline

logger = get_logger(__name__)
DEFAULT_QUERY = "my floor squeaks when I walk on it"


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    payload = run_evidence_pipeline(query)
    logger.info(
        "DemoPipelineResult: %s",
        json.dumps(
            {
                "search_plan": payload["search_plan"],
                "evidence_result": payload["evidence_result"].model_dump(mode="json"),
            },
            indent=2,
        ),
    )


if __name__ == "__main__":
    main()
