# Manual Runs

Quick, human-triggered checks we run when wiring new features or tuning the planner/fetcher stack. This doc separates component smoke tests from end-to-end integration previews. See `docs/reddit_fetcher_baselines.md` for detailed acceptance metrics.

## Component Smoke Tests

### Planner Smoke Test
- **Script:** `scripts/smoke/planner_smoke_test.py`
- **Purpose:** Fast sanity check that the planner can turn a handful of DIY queries into SearchPlans without raising errors.
- **Command:**
  ```bash
  python scripts/smoke/planner_smoke_test.py "How do I hang floating shelves?"
  ```
  (Omit arguments to use the default query list baked into the script.)
- **Expected Output:** Logs showing each query, the returned `plan.query`, and the lists of search_terms/subreddits/notes. Failures surface as logged errors for immediate debugging.
- **Tip:** Use `python scripts/runs/save_plan.py "How do I hang floating shelves?"` when you want to persist a planner output to JSON for later fetcher testing. Files land in `data/plans/` with slugged names.

### Reddit Fetcher Smoke Test
- **Script:** `scripts/smoke/reddit_fetcher_smoke_test.py`
- **Purpose:** Execute the full fetcher pipeline against a real planner-produced SearchPlan. Validates transport, validation, scoring, and comment nesting in one go.
- **Command:**
  ```bash
  python scripts/smoke/reddit_fetcher_smoke_test.py --plan-path data/sample_plan.json --post-limit 5
  ```
  (Load a serialized SearchPlan captured from the planner smoke test or baseline run.)
- **Expected Output:** Structured logs showing the number of candidates fetched, rejection reasons, and accepted posts/comments. Review the emitted FetchResult to confirm URLs, scores, and comments look healthy. For acceptance-rate targets, see `docs/reddit_fetcher_baselines.md`.

## Integration Previews

### Fetch Preview
- **Script:** `scripts/runs/run_fetch_preview.py`
- **Purpose:** Planner + fetcher preview across a query set for manual inspection.
- **Question answered:** “Do we get reasonable posts/comments per query, and how long does it take?”
- **Command:**
  ```bash
  python scripts/runs/run_fetch_preview.py --post-limit 10
  ```
- **Output:** Writes JSON to `data/fetch_previews/` and logs per-query timing plus a final summary.

### Evidence Preview
- **Script:** `scripts/runs/run_evidence_preview.py`
- **Purpose:** Full evidence pipeline preview with optional LLM call.
- **Question answered:** “What evidence request and summary do we produce per query?”
- **Command:**
  ```bash
  python scripts/runs/run_evidence_preview.py --config config/run_config.yaml --mode fixture_only
  ```
- **Output:** Writes JSON to `data/evidence_previews/` (skips write if LLM errors). Logs planner/fetch stats, top scores, and LLM status.

### Stage Summary
- **Script:** `scripts/runs/run_stage_summary.py`
- **Purpose:** Generate pipeline stage summaries for planner, fetch, selector, and evidence output.
- **Question answered:** “What did each stage produce and drop, and why?”
- **Command:**
  ```bash
  python scripts/runs/run_stage_summary.py --config config/run_config.yaml
  ```
- **Output:** Writes JSON to `data/pipeline_stage_summaries/` and logs total runtime.

### Demo Pipeline
- **Script:** `scripts/runs/run_demo_pipeline.py`
- **Purpose:** End-to-end demo run for a single query.
- **Question answered:** “What does the full demo output look like for one query?”
- **Command:**
  ```bash
  python scripts/runs/run_demo_pipeline.py "my floor squeaks when I walk on it"
  ```
- **Output:** Logs a JSON payload (no file output).

### Eval Artifacts Wrapper
- **Script:** `scripts/runs/run_eval_artifacts.py`
- **Purpose:** CLI wrapper for `run_evidence_preview.py` with the same flags.
- **Question answered:** “Can we generate evidence previews via a simplified entry point?”
- **Command:**
  ```bash
  python scripts/runs/run_eval_artifacts.py --config config/run_config.yaml --mode fixture_only
  ```
- **Output:** Same as `run_evidence_preview.py` (JSON + logs).
