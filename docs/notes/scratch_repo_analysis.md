# Scratch: Repo Analysis

## Prompt

Before proceeding, apply these constraints:

- `x_internal/` is private — ignore completely
- `z_legacy/` is deprecated — ignore completely
- `data/archive/` contains old test artifacts — ignore completely
- A `frontend/` directory exists but is out of scope for this analysis (do not analyze deeply)
- Reddit is currently the only data source

Hard constraints:
- Do NOT make any code changes
- Do NOT suggest edits or refactors unless explicitly asked

Do not regenerate the repo map.
Do not rescan the entire repo.

Now perform a focused architectural analysis using the repo map.

Goal:
Understand what the system does and how it works end-to-end.

Instructions:
- Inspect only the most relevant files based on your repo map:
  - entrypoints
  - core services/modules
  - schemas / data models
  - orchestration logic
  - config files
- Determine entrypoints and system flow yourself from the code
- Use docs only if they clarify behavior

Output:
1. 3–5 sentence summary of what the project does
2. End-to-end system flow (user input → final output)
3. Main components and their responsibilities
4. Where key logic lives (orchestration, data handling, model calls, etc.)
5. External services / APIs / models used
6. Evidence vs inference vs unknowns

---

## Response

### 1. What the Project Does

Workbench is a **Reddit-backed evidence retrieval pipeline** for DIY/home improvement queries. Given a natural language question, it uses an LLM to generate a structured search plan, fetches and ranks relevant Reddit threads, then asks a second LLM to curate and return a structured list of ranked source threads with attribution. The output is evidence-first — threads, not summaries or advice.

---

### 2. End-to-End System Flow

```
User query (string)
    │
    ▼
[Planner] agent/planner/core.py
    │  LLM call (gpt-4o-mini, JSON mode)
    │  → SearchPlan: {plan_id, query, search_terms[], subreddits[]}
    │
    ▼
[Reddit Fetcher] services/fetch/reddit_fetcher.py
    │  Concurrent fetch across (subreddit × search_term) pairs
    │  Per post: validate → clean → filter (too short, duplicate, no comments)
    │  Dedup across pairs by post_id
    │  Score candidates:
    │    ├─ (default) Semantic: embed query + each post, cosine similarity
    │    └─ (fallback) Keyword: rule-based relevance scoring
    │  → FetchResult: {posts[], plan_id, query, ...}
    │
    ▼
[Context Builder] services/synthesizer/context_builder.py
    │  Sort by relevance_score, then post_karma
    │  Cap to max_posts
    │  Truncate body/comments to char limits
    │  → EvidenceRequest: {query, plan_id, post_payloads[], config constraints}
    │
    ▼
[Prompt Builder] services/synthesizer/llm_execution/prompt_builder.py
    │  Renders system + user messages
    │  User content = compact JSON of post_payloads
    │  → list[PromptMessage]
    │
    ▼
[LLM Execution] services/synthesizer/llm_execution/llm_client.py
    │  LLM call (gpt-4.1-mini, structured output)
    │  → EvidenceResult: {status, threads[], limitations[], prompt_version}
    │
    ▼
Output dict: {search_plan, evidence_result}
```

There is a second output mode (`pipeline_stage_summary`) that runs the same pipeline but returns diagnostic summaries at each stage boundary instead of the full result.

---

### 3. Main Components and Responsibilities

| Component               | Location                                              | Responsibility                                    |
| ----------------------- | ----------------------------------------------------- | ------------------------------------------------- |
| **Planner**             | `agent/planner/`                                      | LLM → structured search plan (terms + subreddits) |
| **Reddit Fetcher**      | `services/fetch/reddit_fetcher.py`                    | Orchestrates fetch, filter, dedup, and scoring    |
| **Reddit Client**       | `services/reddit_client/`                             | Raw Reddit API calls (search + comments)          |
| **Embedding / Ranking** | `services/embedding/`                                 | Cosine similarity scoring; SQLite embedding cache |
| **Context Builder**     | `services/synthesizer/context_builder.py`             | Post ranking, truncation, and payload assembly    |
| **Prompt Builder**      | `services/synthesizer/llm_execution/prompt_builder.py` | Renders LLM messages from EvidenceRequest        |
| **LLM Client**          | `services/synthesizer/llm_execution/llm_client.py`    | Calls OpenAI and parses EvidenceResult            |
| **Stage Summary**       | `services/synthesizer/stage_summary.py`               | Diagnostic output per pipeline stage              |
| **Demo Pipeline**       | `api/pipeline.py`                                    | Top-level orchestrator; two entry functions       |

`services/context_builder/` contains `ContextBuilderConfig` — a data class for capacity limits. Selection logic lives in `services/synthesizer/context_builder.py`.

---

### 4. Where Key Logic Lives

| Concern                    | Location                                                                                    |
| -------------------------- | ------------------------------------------------------------------------------------------- |
| Orchestration              | `api/pipeline.py` → `_run_pipeline()`                                                      |
| LLM call #1 (planning)     | `agent/planner/core.py:create_search_plan()`                                                |
| LLM call #2 (curation)     | `services/synthesizer/llm_execution/llm_client.py`                                          |
| Fetch concurrency          | `reddit_fetcher.py` — `ThreadPoolExecutor`, controlled by `FETCHER_ENABLE_CONCURRENCY`      |
| Semantic ranking           | `services/embedding/ranking.py` — `rank_candidates()`                                       |
| Keyword ranking (fallback) | `services/fetch/scoring.py` — `evaluate_post_relevance()`                                   |
| Embedding cache            | SQLite at `data/embedding_cache.sqlite3`, via `services/embedding/`                         |
| Subreddit allowlist        | `config/settings.py` → `ALLOWED_SUBREDDITS`; enforced in `agent/planner/model.py` validator |
| Config / limits            | `config/run_config.yaml` → loaded by `api/pipeline.py`                                     |
| Retry / rate limiting      | `services/http/retry_policy.py`                                                             |

---

### 5. External Services / APIs / Models

| Service                           | Usage                                                              |
| --------------------------------- | ------------------------------------------------------------------ |
| **OpenAI gpt-4o-mini**            | Planner (LLM call #1) — hardcoded in `planner/core.py`             |
| **OpenAI gpt-4.1-mini**           | Evidence curator (LLM call #2) — configurable in `run_config.yaml` |
| **OpenAI text-embedding-3-small** | Semantic ranking — configurable via `EMBEDDING_MODEL` env var      |
| **Reddit API**                    | Post search + comment fetch via `services/reddit_client/`          |
| **SQLite**                        | Local embedding cache (`data/embedding_cache.sqlite3`)             |

The settings mention a `pinecone` option for `VECTOR_STORE_TYPE`, but the default (and apparent active path) is `sqlite`.

---

### 6. Evidence vs. Inference vs. Unknowns

**Confirmed from code:**
- Two LLM calls per pipeline run (planner + curator), each using different models
- Semantic ranking is on by default (`USE_SEMANTIC_RANKING=True`) with keyword scoring as an explicit fallback path
- Subreddits are allowlisted and validated at `SearchPlan` construction; the LLM cannot route to arbitrary subreddits
- Concurrent fetching is on by default (`FETCHER_ENABLE_CONCURRENCY=True`, 3 workers)
- The curator LLM is instructed to select/rank only from provided payloads — it does not generate content

**Confirmed from code (follow-up):**
- `api/app.py` — FastAPI app served via uvicorn. Two routes: `GET /` (health check) and `POST /api/run` accepting `{"query": str}`, calls `run_evidence_pipeline()` directly. CORS allows `localhost:5173`.
- `services/http/` — outbound only. Single file (`retry_policy.py`). No inbound API server.
- `services/fetch/comment_pipeline.py` — filters comments by: duplicate ID, AutoModerator, deleted/removed body, karma < 2, minimum length. Survivors sorted by karma descending, capped at 5 per post via hardcoded `MAX_COMMENTS_PER_POST = 5`. This cap is separate from the `max_comments_per_post` limit applied later in the selector.

---

## TODO

### 1. Planner model is hardcoded
- `agent/planner/core.py` hardcodes `gpt-4o-mini`
- Should be configurable, similar to how model is set in `run_config.yaml`

### 2. Unify model usage across planner and summarizer
- Planner uses `gpt-4o-mini`; evidence curator uses `gpt-4.1-mini`
- Choose a single model and centralize configuration

### 3. Clarify selector module structure
- `services/selector/` and `services/summarizer/` renamed to `services/context_builder/` and `services/synthesizer/` — completed
- Ownership of selection logic is ambiguous

---

## Repo Review

### Overall Level

**Strong intermediate / early MVP.** The architecture is more thoughtfully designed than most portfolio projects — real separation of concerns, proper data contracts, and non-trivial infrastructure (semantic ranking, concurrency, retry logic). It reads like someone who understands system design, not just scripting. Not production-ready.

### Strengths

- **Clear pipeline stages with explicit data contracts.** `SearchPlan → FetchResult → EvidenceRequest → EvidenceResult` flows cleanly. Pydantic models at every boundary make the system legible and safe.
- **Semantic ranking with graceful fallback.** Embedding-based scoring with keyword fallback and SQLite cache is solid and pragmatic. The failure path is handled explicitly.
- **Concurrency done correctly.** `ThreadPoolExecutor` with per-task error isolation means one bad (subreddit, term) pair doesn't kill the run.
- **Input validation at the model layer.** Subreddit allowlisting enforced in `SearchPlan` validators is the right place — the LLM cannot hallucinate its way to an unauthorized source.
- **Config-driven pipeline.** `run_config.yaml` + `pydantic-settings` gives the system a credible configuration story without over-engineering.

### Gaps / Risks

- **Planner model is hardcoded.** `gpt-4o-mini` in `planner/core.py` is inconsistent with the rest of the configurable design.
- **Module naming resolved.** `services/selector/` and `services/summarizer/` renamed to `services/context_builder/` and `services/synthesizer/` respectively. Shims in place; callers migrated.
- **Two overlapping comment caps.** `MAX_COMMENTS_PER_POST = 5` hardcoded in `comment_pipeline.py` and `max_comments_per_post` in the selector config are independent limits on the same thing — a silent consistency risk.
- **API layer is a stub.** `api/app.py` has no error handling. A pipeline failure returns an unhandled 500.
- **Orchestrator lives in `demo/`.** `api/pipeline.py` is the core pipeline orchestrator. Burying it under `demo/` understates its role.

### Minimum Fixes Before Demo

1. Make planner model configurable via `run_config.yaml` — closes an obvious inconsistency a reviewer will notice immediately.
2. Add error handling to `POST /api/run` — catch pipeline exceptions and return a structured error response.
3. Resolve the comment cap inconsistency — clarify or consolidate the hardcoded `5` and the selector config value.
4. Rename or restructure the selector modules — even a clear docstring explaining the division is enough.

---

## Proposed Minimal Fixes

### 1. Planner model configuration inconsistency

**Problem:** `agent/planner/core.py` hardcodes `model="gpt-4o-mini"` directly in the API call. The rest of the pipeline reads model config from `run_config.yaml`, so this is an inconsistency that makes the planner invisible to the config layer.

**Fix:**
- Renamed existing `model` key in `run_config.yaml` to `summarizer_model` for clarity; added `planner_model` alongside it — both set to `gpt-4.1-mini`
- Updated `create_search_plan()` to accept an optional `model` parameter, defaulting to `gpt-4.1-mini`
- Updated `api/pipeline.py` and `scripts/runs/run_evidence_preview.py` to read both keys from config and pass `planner_model` through to `create_search_plan()`
- Other callers of `create_search_plan()` (smoke scripts, fetch scripts) use the default and required no changes

**Files modified:** `config/run_config.yaml`, `agent/planner/core.py`, `api/pipeline.py`, `scripts/runs/run_evidence_preview.py`

---

### 2. Missing error handling in the FastAPI demo endpoint

**Problem:** `POST /api/run` calls `run_evidence_pipeline()` with no exception handling. The pipeline raises typed errors (`LLMTransportError`, `LLMStructuredOutputError` from `services/synthesizer/llm_execution/errors.py`, and `RuntimeError` from the planner) — none of these are caught, so any failure surfaces as an unhandled 500 with no structured body.

**Repo context:**
- The pipeline has a typed error hierarchy (`SummarizerLLMError` and subtypes) — these are the right catch targets for downstream failures
- `EvidenceResult` carries `status: Literal["ok", "partial", "error"]` — the response model itself supports an error state
- `run_evidence_pipeline()` returns `{"search_plan": ..., "evidence_result": EvidenceResult}` — error responses should match this shape
- `prompt_version` is required in `EvidenceResult` with no default; it is loaded from config at the start of `_run_pipeline()` before any failure point, so it is always available and should be used — not a placeholder
- No existing API error-handling pattern exists in the repo; this fix establishes one minimally

**Fix Plan:**
- Catch `SummarizerLLMError` (and subtypes) for downstream failures; preserve `search_plan` in the response if the plan was successfully generated before the failure occurred
- Catch `RuntimeError` separately for planner failures, where `search_plan` is genuinely unavailable and should be `None` — note this is a minimal/temporary approach; the planner should eventually raise a typed error like the rest of the pipeline
- Use `prompt_version` from the loaded config in all error responses; do not use empty string or other placeholder values
- Log each failure using `get_logger` consistent with the existing logging pattern
- Do not introduce `HTTPException` or a new error model — use `EvidenceResult` as the response contract so the frontend sees a consistent shape regardless of outcome

**Files likely affected:** `api/app.py`

---

### 3. Hardcoded comment cap in `comment_pipeline.py`

**Problem:** `MAX_COMMENTS_PER_POST = 5` is hardcoded as a module-level constant in `services/fetch/comment_pipeline.py`. The context builder already has a `max_comments_per_post` field in `ContextBuilderConfig`. Two separate caps on the same thing with no explicit relationship is a silent correctness risk.

**Fix (complete):**
- Moved cap into `config/settings.py` as `FETCHER_MAX_COMMENTS_PER_POST: int = 5` with a description documenting its distinction from `ContextBuilderConfig.max_comments_per_post`
- Removed `MAX_COMMENTS_PER_POST` module-level constant from `comment_pipeline.py`
- Added `max_comments: int = 5` parameter to `filter_comments()`; updated docstring to clarify the two-cap distinction
- Updated `reddit_fetcher.py` to pass `settings.FETCHER_MAX_COMMENTS_PER_POST` explicitly

**Files modified:** `config/settings.py`, `services/fetch/comment_pipeline.py`, `services/fetch/reddit_fetcher.py`

**Edge case fix (complete):** Changed `filter_comments()` default from `max_comments=5` to `max_comments=settings.FETCHER_MAX_COMMENTS_PER_POST`. Added `from config.settings import settings` import. Magic number fully removed.

---

## Remaining TODOs

### FastAPI error handling — not yet implemented

`POST /api/run` still has no exception handling. See fix plan in ### 2 above.

### Clarify selector module structure

- `services/selector/` (contains only `SelectorConfig`) and `services/summarizer/selector.py` (contains actual selection logic) have overlapping names and unclear separation of responsibilities
- Ownership of selection logic is ambiguous — needs either a rename, a structural consolidation, or at minimum clear docstrings establishing the boundary

### Orchestrator lives in `demo/`

- `api/pipeline.py` is the core pipeline orchestrator but is buried under `demo/`, coupling it to the demo context
- Should be moved to a top-level location (e.g., `pipeline/` or `agent/`) so it is clearly a first-class component, not a demo artifact

### Happy Path Quality Check 
❯ Inspect the log output from this run:

/Users/mallan/dev/workbench-mvp/logs/run_demo_pipeline_03-25-26.log

Evaluate:
1. Structured output quality
- Are the LLM outputs well-formed and aligned with their schemas?
- Do they look semantically coherent and useful (not generic or nonsensical)?

1. Signal vs noise
- Does the system appear to be selecting and summarizing meaningful content?
- Or does anything look shallow, repetitive, or low-quality?

Constraints:
- Do NOT suggest improvements or refactors
- Do NOT comment on code or architecture
- This is evaluation only

Output:
- Short verdict (2–3 sentences): “credible”, “borderline”, or “weak”
- 3–5 bullet observations supporting that verdict

Verdict: Credible.
  The pipeline ran cleanly end-to-end, the output is well-formed and schema-compliant, and the results are semantically
  on-target for the query.

  - Search plan is sharp. Four search terms (floor squeak repair, fix squeaky floorboards, floor joist squeaking, squeaky
  hardwood floor solution) are specific and well-varied — not just synonyms of each other.
  - Thread selection is directly relevant. All 5 ranked threads are unambiguously about squeaky floor repair, from appropriate
  subreddits. No off-topic drift.
  - Relevance scores are tightly clustered (~0.631–0.644), which is honest — these are genuinely similar posts. The LLM
  correctly selected the top 5 rather than padding with weaker results.
  - Limitations are accurate and specific, not boilerplate. "Fix methods rather than causes" and "anecdotal with varying floor
  types" reflect the actual content of the threads.
  - Status ok is correctly applied — 5 results returned with no apparent evidence gaps that would warrant partial.
