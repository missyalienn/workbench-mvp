**Observability Implementation Plan**
This document is the implementation outline for the logging + artifact system
defined in `docs/logging.md`. It is a step-by-step execution plan with concrete
files, functions, and outputs.

**Scope**
- Logging stages and required fields per `docs/logging.md`
- Artifact outputs: `run_report.json`, `stage_diagnostics.json`, `evidence_result.json`
- API runner (`demo/app.py`) and CLI runners (`scripts/`)

**Step 1: Lock Contracts**
Goal: ensure the team agrees on names and fields before code changes.
1. Confirm canonical stage names and required fields in `docs/logging.md`.
2. Confirm artifact names and purposes in `docs/logging.md`.
3. Decide whether API runs will write artifacts or remain log-only.

**Step 2: Add Shared Run Helpers**
Goal: avoid duplicated logic for run identity, sanitization, and timing.
1. Create a small helper module, `services/observability/run_context.py`. (Done)
2. Functions to include:
   - `generate_run_id() -> str` (Done)
   - `sanitize_query(query: str, max_len: int = 120) -> str` (Done)
   - `elapsed_ms(start_time: float) -> int` (Done)
3. Ensure type hints on all functions. (Done)

**Step 3: Pipeline Stage Logging**
Goal: emit canonical stage logs from the pipeline core.
1. File: `demo/pipeline.py` (Done)
2. Add stage logs around:
   - `pipeline_start` (Done)
   - `planner_start` / `planner_end` around `create_search_plan` (Done)
   - `fetch_start` / `fetch_end` around `run_reddit_fetcher` (Done)
   - `embedding_start` / `embedding_end` inside `run_reddit_fetcher` around semantic ranking (Done)
   - `context_start` / `context_end` around `build_summarize_request` + `build_messages` (Done)
   - `llm_start` / `llm_end` around `summarize_structured` (Done)
   - `pipeline_end` (Done)
3. Required fields on every stage log:
   - `run_id`, `stage`, `event`, `status`, `duration_ms`, `query` (sanitized) (Done)
4. Stage-specific fields:
   - Planner: `plan_id`, `num_terms`, `num_subreddits`
   - Fetch: `plan_id`, `tasks`, `post_limit`, `accepted_posts`
   - Embedding: `embedding_model`, `candidates_scored`
   - Context: `selected_posts`, `total_posts`
   - LLM: `model`, `prompt_version`
   - Pipeline end: `threads`, `limitations_count`

**Step 4: API Request Logging**
Goal: add request boundary logs and propagate `run_id`.
1. File: `demo/app.py` (Done)
2. On entry:
   - Generate `run_id` (Done)
   - Log `request_start` with `run_id`, `query` (sanitized) (Done)
3. Call the canonical pipeline entrypoint with `run_id`.
4. On exit:
   - Log `request_end` with `run_id`, `status`, `duration_ms` (Done)

**Step 4b: Structured Logging Consistency**
Goal: make stage logs parseable and consistent.
1. Use `key=value` pairs in all stage logs. (Done)
2. Include `event` on start/end/error logs. (Done)
3. For errors, include `error_type`, `error_message`, and `reason` fields. (Done for embedding stage)

**Step 5: Artifact Writers (CLI First)**
Goal: standardize artifact outputs and directory layout.
1. Create a writer module, suggested path `services/observability/artifacts.py`.
2. Functions to include:
   - `write_run_report(...) -> Path`
   - `write_stage_diagnostics(...) -> Path`
   - `write_evidence_result(...) -> Path`
3. Output directory:
   - `data/runs/<timestamp>_<run_id>/`
4. Artifact contents:
   - `run_report.json` includes metadata, config snapshot, timings, counts, status,
     and pointers to other artifacts.
   - `stage_diagnostics.json` includes fetch candidates, context selection, evidence
     selection, and diffs.
   - `evidence_result.json` includes the full `EvidenceResult`.

**Step 6: Align CLI Runners**
Goal: all batch runs use the same pipeline entrypoint and artifact schema.
1. `scripts/run_demo_pipeline.py`
   - Use canonical pipeline entrypoint.
   - Write `run_report.json` and `evidence_result.json`.
2. `scripts/run_stage_summary.py`
   - Use canonical pipeline entrypoint.
   - Write `run_report.json` and `stage_diagnostics.json`.
3. `scripts/run_evidence_preview.py`
   - Prefer routing through canonical pipeline entrypoint where possible.
   - If it must stay specialized, ensure artifacts match the new schema.
4. Optional: add `scripts/run_batch.py` and deprecate older scripts.

**Step 7: Add Tests**
Goal: keep new logic deterministic and safe.
1. Add tests for:
   - `generate_run_id()` format
   - `sanitize_query()` truncation behavior
   - Artifact writer outputs (file names and required fields)
2. Use fixed timestamps in tests to avoid flakiness.

**Step 8: Validation Runs**
Goal: ensure behavior matches the spec.
1. One API run via `/api/demo`:
   - Verify stage logs and request logs.
2. One CLI batch run:
   - Verify artifact directory and filenames.
   - Validate artifact JSON structure.

**Step 9: Deprecate Legacy Outputs**
Goal: avoid confusing mixed formats.
1. Ensure legacy artifact paths are no longer written.
2. Leave comments in legacy scripts if they are still present.
3. Keep `data/archive/20260320_preobs/` as the historic snapshot.
