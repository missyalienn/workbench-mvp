## Semantic vs Keyword Comparison (Pipeline Stage Summary)

Date: 2026-03-17

### Why this exists
- Keyword ranking was a temporary scaffold, not the intended design.
- This comparison checks that semantic is at least as good on a fixed query set.

### Commands used
- Keyword run (semantic off):
  - `USE_SEMANTIC_RANKING=false python scripts/runs/run_stage_summary.py`
- Semantic run:
  - `USE_SEMANTIC_RANKING=true python scripts/runs/run_stage_summary.py`

### Output files used
- Keyword: `data/pipeline_stage_summaries/semanticFALSE_pipeline_stage_summary_2026-03-17_202924.json`
- Semantic: `data/pipeline_stage_summaries/semanticTRUE_pipeline_stage_summary_2026-03-17_203338.json`

### Top-N counts (evidence threads)

| Query | Semantic top-N | Keyword top-N |
| --- | --- | --- |
| how to caulk a bathtub | 5 | 2 |
| how to repair holes in drywall | 5 | 4 |
| how to bleed a radiator | 3 | 3 |
| how to hang floating wall shelves | 3 | 2 |
| how to remove scratches from wood table | 5 | 1 |

### Per-query notes

#### how to caulk a bathtub
- Semantic top-N count: 5
- Keyword top-N count: 2
- Notes:
  - Semantic threads are all directly about caulking tubs (prep, re-caulk, tape, troubleshooting).
  - Keyword results skew to troubleshooting-only and are narrower in coverage.
  - Semantic gives broader, more instruction-oriented coverage.

#### how to repair holes in drywall
- Semantic top-N count: 5
- Keyword top-N count: 4
- Notes:
  - Both modes are relevant, but semantic includes more direct “how to fix” threads.
  - Keyword includes a plaster-repair thread that is adjacent, not drywall-specific.
  - Semantic is more consistently on-topic across the top-N.

#### how to bleed a radiator
- Semantic top-N count: 3
- Keyword top-N count: 3
- Notes:
  - Semantic threads explicitly mention bleeding radiators and bleed valves.
  - Keyword threads skew to stuck valves and system diagnosis.
  - Semantic is closer to the user’s exact intent.

#### how to hang floating wall shelves
- Semantic top-N count: 3
- Keyword top-N count: 2
- Notes:
  - Semantic includes direct “how to hang/install” threads.
  - Keyword threads are relevant but more indirect (reinforcing studs, avoiding wall damage).
  - Semantic is more instruction-focused.

#### how to remove scratches from wood table
- Semantic top-N count: 5
- Keyword top-N count: 1
- Notes:
  - Semantic returns multiple scratch-repair threads (finish damage, deep scratches).
  - Keyword returns a single epoxy-table thread (narrow scope).
  - Semantic has clearly stronger coverage and variety.

### Quick takeaway
- Semantic is **not worse** than keyword on this fixed query set.
- Semantic usually returns **more** clearly relevant top-N threads.
- Keyword was never the intended design; semantic is the target approach.

### One‑liner you can reuse
“Keyword was a temporary baseline; semantic is the intended approach. On a fixed query set, semantic stays on‑topic with broader coverage and no obvious regressions.”
