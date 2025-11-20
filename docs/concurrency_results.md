## Reddit Fetcher Concurrency Results

- **Queries:** Default preview list (10 queries) for all measurements.
- **Command:** `python -m scripts.run_fetch_preview --post-limit 10` (same options each time).
- **Artifacts:** Preview JSONs saved under `data/fetch_previews/` for each timing run.
- **Observability:** No warnings about `RateLimitError` or `RetryableFetchError` appeared in any run (logs stayed at INFO level only).

### Timing Summary
| Run Mode                | `FETCHER_ENABLE_CONCURRENCY` | `FETCHER_MAX_WORKERS` | Total Time (10 queries) | Preview Artifact                                                  |
| ----------------------- | ---------------------------- | --------------------- | ----------------------- | ----------------------------------------------------------------- |
| Serial Baseline         | False                        | n/a                   | ~102 s                  | `data/fetch_previews/fetch_preview_20251120_serial_baseline.json` |
| Threaded (Conservative) | True                         | 2                     | ~76.5 s                 | `data/fetch_previews/fetch_preview_20251120_threaded2.json`       |
| Threaded (Current)      | True                         | 3                     | ~54.4 s                 | `data/fetch_previews/fetch_preview_20251120_threaded3.json`       |

### Notes
- Multithreading yielded a ~25% speedup with 2 workers and ~47% with 3 workers compared to the serial baseline.
- No rate-limit hits or post-fetch retries were observed in any run.
- All runs used the same 10 queries; order differences in output are expected due to concurrency.
- Logs aren’t persisted, so timings are inferred from the new INFO-level duration logs added to `scripts/run_fetch_preview.py`.
