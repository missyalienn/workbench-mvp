**Logging Source Of Truth**
This document defines the single, consistent logging approach for the evidence pipeline
and its runners (API + CLI). All new logs and refactors must align to this spec.

**Goals**
1. One pipeline entrypoint, one logging schema.
2. Consistent stage boundaries across API and batch CLI.
3. Clear per-request and per-query timings.
4. Minimal but sufficient logs for debugging and observability.

**Scope**
- Pipeline orchestration in `demo/pipeline.py`
- API entrypoint in `demo/app.py`
- Batch CLI runner in `scripts/run_batch.py` (future)
- Shared services in `agent/` and `services/`

**Core Principles**
- Log at stage boundaries, not every internal step.
- Use structured, consistent fields in every log line.
- Prefer `INFO` for stage lifecycle, `WARNING` for recoverable issues,
  `ERROR` for failures, and `DEBUG` for deep diagnostics.
- Never log secrets or full raw user content.
- Every pipeline run must emit a `run_id`.

**Structured Logging Format**
- Emit stage logs using `key=value` pairs to keep logs parseable.
- Include `event` to distinguish start/end/error/other sub-events.
- Example: `stage=fetch_end event=end run_id=abc123 status=ok duration_ms=812`
- When `LOG_FORMAT_TYPE=json`, the logger will also emit JSON with `plan_id`.

**Canonical Stages**
All runs must log the same stage names in this order:
1. `request_start` (API only)
2. `pipeline_start`
3. `planner_start` / `planner_end`
4. `fetch_start` / `fetch_end`
5. `embedding_start` / `embedding_end` (semantic ranking inside fetch when enabled)
6. `context_start` / `context_end` (selector + prompt build)
7. `llm_start` / `llm_end`
8. `pipeline_end`
9. `request_end` (API only)

**Stage To Code Mapping**
- `request_start` / `request_end`: `demo/app.py` (`run_demo`)
- `pipeline_start` / `pipeline_end`: `demo/pipeline.py` (`_run_pipeline`)
- `planner_start` / `planner_end`: `agent/planner/core.py` (`create_search_plan`)
- `fetch_start` / `fetch_end`: `services/fetch/reddit_fetcher.py` (`run_reddit_fetcher`)
- `embedding_start` / `embedding_end`: `services/embedding/ranking.py` (query + post embeddings)
- `context_start` / `context_end`: `services/summarizer/selector.py` and `services/summarizer/llm_execution/prompt_builder.py`
- `llm_start` / `llm_end`: `services/summarizer/llm_execution/llm_client.py` (`summarize_structured`)

**Required Log Fields**
Every `INFO` stage log must include:
- `run_id`
- `stage`
- `status` (e.g., `ok`, `error`)
- `duration_ms` (stage duration, or total for start/end)
- `query` (sanitized or truncated)

Stage-specific fields:
- Planner: `plan_id`, `num_terms`, `num_subreddits`
- Fetch: `plan_id`, `tasks`, `post_limit`, `accepted_posts`
- Embedding: `embedding_model`, `candidates_scored`
- Context: `selected_posts`, `total_posts`
- LLM: `model`, `prompt_version`
- Pipeline end: `threads`, `limitations_count`

**Run Identity**
- Generate a `run_id` at the very start of each run (API or CLI).
- Include `run_id` in all downstream logs.

**Sanitization Rules**
- `query` should be truncated to a max length (e.g., 120 chars).
- Do not log raw prompt content or full LLM messages.
- Do not log credentials or tokens.

**API Runner (Frontend)**
- `demo/app.py` logs:
  - `request_start` with `run_id`, `query_preview`
  - `request_end` with `run_id`, `status`, `duration_ms`
- It should call the canonical pipeline entrypoint and pass `run_id`.

**Batch CLI Runner**
- `scripts/run_batch.py` (preferred runner):
  - `batch_start` with `num_queries`
  - For each query: full pipeline stage logs using the same schema
  - `batch_end` with total duration and success/error counts
- Existing scripts should be folded into this runner over time.

**Artifact Outputs**
- Avoid the word "summary" in artifact names.
- CLI outputs should be written to `data/runs/<timestamp>_<run_id>/...`
- API runs should be log-only by default.
- If artifacts are needed for API, they should use the same directory scheme.

**Canonical Artifact Names**
1. `run_report.json`
2. `stage_diagnostics.json`
3. `evidence_result.json`

**Artifact Contents and Purpose**
**`run_report.json`**
Purpose: a single, durable record of the run.
Questions answered:
- What ran, when, and with what configuration?
- How long did each stage take?
- How much content flowed through each stage?
Contents:
- run metadata: `run_id`, `timestamp`, `query` (sanitized)
- config snapshot: `model`, `prompt_version`, `post_limit`, `allow_llm`
- timings: total + per stage
- counts: `posts_fetched`, `posts_selected`, `threads_returned`
- status: `ok` or `error`
- artifact pointers: filenames for `stage_diagnostics.json` and `evidence_result.json`

**`stage_diagnostics.json`**
Purpose: trace selection decisions across stages.
Questions answered:
- Which items were dropped and why between fetch, context, and evidence?
- Which items made it through each stage?
Contents:
- fetch candidates (id, score, subreddit, url, comment count)
- context selection (post ids in LLM input)
- evidence selection (post ids in final output)
- diffs: dropped before context, in context but not in evidence

**`evidence_result.json`**
Purpose: the final model output used by the app.
Questions answered:
- What evidence threads and limitations were produced?
Contents:
- full `EvidenceResult` payload only

**Best Practice: How To Fold This Into Docs**
1. Keep this file (`docs/logging.md`) as the source of truth for both logs and artifacts.
2. Add a short link from `README.md` to `docs/logging.md`.
3. When adding a new runner or stage, update this doc first.
4. Keep a single canonical artifact naming scheme and deprecate old names in code comments.

**Example Log Lines**
```text
INFO demo.pipeline: stage=pipeline_start event=start run_id=abc123 query="how to caulk a bathtub"
INFO agent.planner.core: stage=planner_end event=end run_id=abc123 plan_id=plan_01 duration_ms=812 num_terms=3 num_subreddits=4 status=ok
INFO services.fetch.reddit_fetcher: stage=fetch_end event=end run_id=abc123 plan_id=plan_01 duration_ms=1632 tasks=12 post_limit=10 accepted_posts=7 status=ok
INFO services.summarizer.selector: stage=context_end event=end run_id=abc123 duration_ms=42 total_posts=7 selected_posts=5 status=ok
INFO services.summarizer.llm_execution: stage=llm_end event=end run_id=abc123 duration_ms=2140 model=gpt-4.1-mini prompt_version=v3 status=ok
INFO demo.pipeline: stage=pipeline_end event=end run_id=abc123 duration_ms=4819 threads=4 limitations_count=1 status=ok
INFO demo.app: stage=request_end event=end run_id=abc123 duration_ms=4892 status=ok
```

**Compliance Checklist**
1. Every entrypoint emits `run_id`.
2. All canonical stages are logged in order.
3. All required fields are present.
4. No secrets or raw prompts are logged.
