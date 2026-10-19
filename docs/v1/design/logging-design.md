# Logging Design

## Infrastructure (`config/logging_config.py`)

- `configure_logging()` — configures structlog globally. Text mode (default) uses `ConsoleRenderer`; JSON mode (`LOG_FORMAT_TYPE=json`) uses `JSONRenderer`. Also calls `logging.basicConfig` so third-party libs (openai, httpx, etc.) still emit to stderr.
- `get_logger(name)` — returns a structlog `BoundLogger`. All modules use this.
- `plan_context_scope(plan_id)` — context manager that calls `structlog.contextvars.bind_contextvars(plan_id=plan_id)` on entry and `clear_contextvars()` on exit. Any log line emitted while this scope is active automatically includes `plan_id`.

## Settings (`config/settings.py`)

- `LOG_LEVEL` — controls verbosity (default `INFO`). Set to `DEBUG` to see per-post and per-comment rejection logs.
- `LOG_FORMAT_TYPE` — `"text"` (default, human-readable) or `"json"` (structured, production-ready).

## Log call style

All call sites use structured event keys with keyword arguments:

```python
logger.info("fetch.post_rejected", reason="too_short", post_id=post_id)
logger.info("pipeline.complete", elapsed_ms=240, status="ok", n_threads=3)
```

Event keys follow a `service.event` convention (e.g. `fetch.start`, `planner.complete`, `embedding.cache_read_failed`).

## Log levels

| Level | Usage |
|---|---|
| `INFO` | Pipeline lifecycle events, stage start/complete with `elapsed_ms`, token refresh |
| `WARNING` | Recoverable failures: request errors, ranking fallback, cache failures |
| `DEBUG` | Per-post and per-comment rejection reasons (duplicate, too_short, automoderator, etc.) |
| `ERROR` | Unrecoverable failures: LLM transport errors, missing credentials |

Third-party loggers (openai, httpx, httpcore, keyring, urllib3, markdown_it) are pinned to `WARNING` in `configure_logging()` to suppress routine chatter.

## `plan_id` propagation

`plan_context_scope` is entered at two levels:

1. **Planner** (`agent/planner/core.py`) — wraps the LLM call that generates the plan.
2. **Pipeline orchestrator** (`api/pipeline.py`) — wraps the full fetch/build/synthesize sequence after the plan is created, using `plan_context_scope(str(plan.plan_id))`.

This means every log line emitted during a pipeline run — across the fetcher, ranker, context builder, and synthesizer — carries `plan_id`.

### ThreadPoolExecutor workers

structlog's contextvars are stored in Python's `contextvars.Context`, which does **not** automatically propagate into threads spawned by `ThreadPoolExecutor`. Without intervention, worker thread logs (post rejection, comment filtering, etc.) would lack `plan_id`.

**Fix:** `_context_wrapper` in `services/fetch/reddit_fetcher.py` captures a snapshot of the calling thread's context via `copy_context()` at dispatch time, then runs the worker inside it via `ctx.run(fn, **kwargs)`. The submit call becomes:

```python
executor.submit(_context_wrapper, _fetch_posts_for_pair, subreddit=subreddit, ...)
```

This ensures `plan_id` is visible in all worker thread logs with no changes to the worker function itself.

## Retry logging

`services/http/retry_policy.py` uses a stdlib `logging.getLogger` (not structlog) exclusively for passing to tenacity's `after_log`. This is intentional — tenacity requires a stdlib `Logger` interface. Retry attempt logs will not carry structlog context fields.

## Per-stage timing

All major pipeline stages log `elapsed_ms` on completion:

| Stage | Event key |
|---|---|
| Planner | `planner.complete` |
| Fetcher | `fetch.complete` |
| Ranker | `ranking.complete` |
| Context builder | `context.complete` |
| Synthesizer | `synthesizer.complete` |
| Full pipeline | `pipeline.complete` |
