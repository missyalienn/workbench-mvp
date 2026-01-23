"""CLI wrapper for generating eval artifacts from evidence previews."""
# Run: python scripts/run_eval_artifacts.py --config config/evidence_preview.yaml --mode fixture_only

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_evidence_preview import app


if __name__ == "__main__":
    app()
