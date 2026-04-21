# CLAUDE.md — workbench-mvp
> Extends ~/.claude/CLAUDE.md. Do not repeat global rules here.

## Stack
- Language: Python 3.12+
- Framework: FastAPI
- Package manager: uv / pyproject.toml
- Test runner: pytest
- Linter / formatter: ruff, black
- Type checker: mypy

## Commands
```bash
# Tests
pytest

# Single test
pytest tests/path/to/test_file.py::test_function_name

# Type check
mypy <module>

# Lint / format
ruff check .
black .

# End-to-end demo
python scripts/runs/run_demo_pipeline.py "query string"

# Fetch + planner preview
python scripts/runs/run_fetch_preview.py --post-limit 10

# Evidence pipeline preview
python scripts/runs/run_evidence_preview.py --config config/run_config.yaml --mode fixture_only
```

## Architecture
Reddit research pipeline: accepts a natural language query, fetches and ranks Reddit evidence, returns a structured synthesis via LLM.

```
planner → fetcher → ranking → context_builder → synthesizer
```

| Stage | Location | Responsibility |
|---|---|---|
| Planner | `agent/planner/` | Turns query into structured `SearchPlan` via OpenAI |
| Fetcher | `services/fetch/` | Fetches Reddit posts/comments; returns `FetchResult` |
| Ranking | `services/embedding/ranking.py` | Cosine similarity scoring; falls back to karma sort |
| Context builder | `services/context_builder/` | Selects top posts, truncates to token budget, builds `EvidenceRequest` |
| Synthesizer | `services/synthesizer/` | LLM call via OpenAI Responses API; returns `EvidenceResult` |

**Supporting modules:**
- `config/settings.py` — Pydantic settings, env-driven; `config/run_config.yaml` — runtime tuning
- `services/http/retry_policy.py` — generic `build_retry(is_retryable)` factory; each client owns its retry predicate
- `services/reddit_client/` — Reddit API client with retry predicate
- `services/embedding/` — OpenAI embeddings with SQLite cache
- `config/logging_config.py` — structlog setup; `get_logger()` and `plan_context_scope()`

## Entry Points
Read these before proposing changes:
- `api/pipeline.py` — pipeline wiring, main execution path
- `config/settings.py` — all env vars and runtime config
- `services/synthesizer/`, `services/context_builder/` — core types; read before any API changes

## Logging
All modules use `get_logger(name)` from `config/logging_config.py` (returns structlog `BoundLogger`).
- Event key convention: `service.event` (e.g. `fetch.post_rejected`, `pipeline.complete`)
- `plan_context_scope(plan_id)` — binds `plan_id` to all log lines in a pipeline run, including worker threads (propagated via `copy_context()`)

## Dependency Violations (this stack)
- Introduce `ABC` or `typing.Protocol` in the inner layer; outer layer implements it
- Never pass FastAPI `Request`, `Response`, or ORM models into domain or application logic

## Do Not Touch
`x_internal/` and `z_legacy/` — archived; excluded from pytest.

## Production Notes
- Prefer production-aligned boundaries over demo shortcuts
- Infer patterns from hardened service layers, not the app layer
- Preserve typed failure semantics; avoid ad hoc route-level exception mapping
- Do not leak raw tracebacks or internal errors to API clients
- `EvidenceResult.status` (`ok | partial | error`) is an LLM research quality signal — not a system health contract; do not use for HTTP status mapping
