"""Generate a SearchPlan JSON file with a unique name."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from agent.planner.core import create_search_plan
from config.logging_config import get_logger

logger = get_logger(__name__)
app = typer.Typer(add_completion=False)


@app.command()
def run(query: str = typer.Argument(..., help="User query for SearchPlan generation.")) -> None:
    output_dir = Path("data/plans")
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = create_search_plan(query)

    short_id = plan.plan_id.hex[:8]
    filename = f"plan_{short_id}.json"
    path = output_dir / filename
    path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    logger.info("Saved plan to %s", path)


if __name__ == "__main__":
    app()
