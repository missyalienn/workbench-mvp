# CLAUDE.md
> Extends ~/.claude/CLAUDE.md. Do not repeat global rules here.

## Stack
- Language: Python 3.12+
- Framework: FastAPI
- Package manager: uv / pyproject.toml
- Test runner: pytest
- Linter / formatter: ruff, black
- Type checker: mypy

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run a single test file or test
pytest tests/path/to/test_file.py::test_function_name

# End-to-end demo run
python scripts/runs/run_demo_pipeline.py "my floor squeaks when I walk on it"

# Fetch + planner preview
python scripts/runs/run_fetch_preview.py --post-limit 10

# Full evidence pipeline preview
python scripts/runs/run_evidence_preview.py --config config/run_config.yaml --mode fixture_only

# Type check
mypy <module>
```

## Architecture

Pipeline stages (in order):

```
planner → fetcher → ranking → context_builder → synthesizer
```

| Stage           | Location                        | What it does                                                                                         |
| --------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Planner         | `agent/planner/`                | Turns query into a structured `SearchPlan` via OpenAI                                                |
| Fetcher         | `services/fetch/`               | Fetches Reddit posts/comments; filters and validates raw data; assembles internal `PostCandidate` intermediates and returns structured `Post` objects in `FetchResult` |
| Ranking         | `services/embedding/ranking.py` | Scores candidates via cosine similarity against query embedding; falls back to karma sort on failure |
| Context builder | `services/context_builder/`     | Selects top posts, truncates to token budget, builds `EvidenceRequest`                               |
| Synthesizer     | `services/synthesizer/`         | Executes LLM call (OpenAI Responses API); returns structured `EvidenceResult`                        |

Pipeline is wired in `api/pipeline.py`. The FastAPI app is in `api/app.py`.

**Key supporting modules:**
- `config/settings.py` — Pydantic settings, env-driven; `config/run_config.yaml` — runtime tuning
- `services/http/retry_policy.py` — generic `build_retry(is_retryable)` factory; each client owns its own predicate
- `services/reddit_client/` — Reddit API client; retry predicate defined here
- `services/embedding/` — OpenAI embeddings with SQLite cache; retry predicate defined here
- `config/logging_config.py` — structlog setup; `get_logger()` and `plan_context_scope()`

## Logging

All modules use `get_logger(name)` from `config/logging_config.py` (returns a structlog `BoundLogger`).

Event keys follow `service.event` convention: `fetch.post_rejected`, `pipeline.complete`, etc.

`plan_context_scope(plan_id)` is a context manager that binds `plan_id` to all log lines in a pipeline run, including worker threads (propagated via `copy_context()`).

## Production Hardening Notes 

Some API and app-layer code was built for demo speed and is not necessarily the intended long-term production design. Do not assume current route shapes or direct pipeline passthroughs are final architecture.

When proposing changes:

* prefer production-aligned boundaries over preserving demo shortcuts
* infer patterns from the hardened parts of the repo, not just the thinnest app layer
* preserve typed failure semantics as long as possible
* avoid ad hoc route-level exception mapping as the primary design
* do not leak raw tracebacks or internal errors to API clients
* keep domain output semantics separate from system/runtime failure handling

`EvidenceResult.status` (`ok | partial | error`) is an LLM-generated research quality signal — it reflects evidence sufficiency, not system health. It is not an API/system failure contract and should not be used for error handling or HTTP status mapping.




## Do Not Touch

`x_internal/` and `z_legacy/` — archived; excluded from pytest.
