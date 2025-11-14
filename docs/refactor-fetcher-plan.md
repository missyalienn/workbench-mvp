
Focused 4-day plan (≈8 hours/day) to stabilize the fetcher, add resilience, and ship a synthesis-ready demo. “Happy path” lists the minimum critical work; “Extras (if time)” captures nice-to-haves we’ll skip unless everything else is done.

---

## Day 1 – Modularize the Fetcher

**Happy Path (Critical)**
- Extract a `reddit_client.py` API client wrapper that owns session setup and raw search/comment calls (no behavior change yet).
- Keep `reddit_validation.py` focused on veto/business rules; ensure the fetcher calls helpers instead of raw fields.
- Move post/comment builders into a dedicated assembly module (e.g., `reddit_assembly.py`).
- Rewire `run_reddit_fetcher` to use the new modules in order (client → validation → assembly) and re-run preview/eval scripts to confirm identical results.

**Extras (If Time)**
- Add lightweight unit tests for each module (mocked API client, validation cases).
- Improve docstrings/README diagrams reflecting the new module boundaries.

**Deliverable**
- Modular fetcher with no functional regressions; baseline preview/eval JSON proving parity.

**Progress Notes (2025-11-12)**
- `services/reddit_client/` now houses session handling, raw endpoints, and a high-level client; `reddit_fetcher` relies on it.
- Post/comment builders, content filters, and the comment pipeline each live in dedicated modules (`reddit_builders.py`, `content_filters.py`, `comment_pipeline.py`).
- Verified the refactor by running `python -m scripts.run_fetch_preview` (see `data/fetch_previews/fetch_preview_20251112_refactor.json`).
- TODO: add unit tests for the new helper modules (tracked inline) and continue monitoring whether the comment pipeline should expose additional helpers.

**Current Work Breakdown**
1. Build the new `services/reddit_client/` package (session manager, API client, endpoints) and update `reddit_fetcher.py` to consume it.
2. Move assembly helpers into `reddit_assembly.py` and validate imports.
3. Write minimal unit tests for the new modules (session auth, client methods, assembly helpers).
4. Update docs (e.g., `reddit_fetcher_design.md`) once the refactor is confirmed working.

**Helper Inventory (Current → Target)**  
_Functions currently implemented inside `services/fetch/reddit_fetcher.py`._

| Function / Helper         | Function Signature                                                       | Purpose                                       | Target Module        |
|--------------------------|---------------------------------------------------------------------------|-----------------------------------------------|----------------------|
| `_get_client`            | `def _get_client(environment: str = "dev") -> Session`                    | Build authenticated `requests.Session`        | `reddit_client.py`   |
| `search_subreddit`       | `def search_subreddit(subreddit: str, query: str, limit: int = 25, after: str \| None = None, environment: str = "dev") -> dict` | Call Reddit search endpoint | `reddit_client.py` |
| `paginate_search`        | `def paginate_search(subreddit: str, query: str, limit: int, environment: str = "dev") -> Iterator[dict]` | Iterate through search pages | `reddit_client.py` |
| `fetch_comments`         | `def fetch_comments(post_id: str, limit: int = 50, environment: str = "dev") -> list[dict]` | Fetch top-level comments for a submission | `reddit_client.py` |
| `passes_post_validation` | `def passes_post_validation(raw_post: dict[str, Any]) -> bool`            | Run metadata veto checks                      | `reddit_validation.py` |
| `is_post_too_short`      | `def is_post_too_short(body: str) -> bool`                                | Enforce minimum body length                   | `reddit_validation.py` |
| `has_seen_post`          | `def has_seen_post(post_id: str, seen_post_ids: set[str]) -> bool`        | Deduplicate posts per run                     | `reddit_validation.py` |
| `filter_comments`        | `def filter_comments(post_id: str, raw_comments: list[dict[str, Any]]) -> list[dict[str, Any]]` | Apply comment-level vetoes | `reddit_validation.py` |
| `is_comment_too_short`   | `def is_comment_too_short(body: str) -> bool`                             | Enforce minimum comment length                | `reddit_validation.py` |
| `has_seen_comment`       | `def has_seen_comment(comment_id: str, seen_comment_ids: set[str]) -> bool` | Deduplicate comments per run                | `reddit_validation.py` |
| `_build_comment_payload` | `def _build_comment_payload(*, comment_id: str, post_id: str, cleaned_body: str, comment_karma: int) -> dict[str, Any]` | Normalize filtered comment data | `reddit_assembly.py` |
| `build_comment_models`   | `def build_comment_models(filtered_comments: list[dict[str, Any]], fetched_at: float) -> list[Comment]` | Convert payloads into `Comment` objects | `reddit_assembly.py` |
| `build_post_model`       | `def build_post_model(*, raw_post: dict[str, Any], cleaned_title: str, cleaned_body: str, relevance_score: float, matched_keywords: list[str], comments: list[Comment], fetched_at: float) -> Post` | Construct `Post` objects from cleaned data | `reddit_assembly.py` |
| `post_permalink`         | `def post_permalink(raw_post: dict[str, Any]) -> str`                     | Produce canonical Reddit URL for a submission | `reddit_assembly.py` |


---

## Day 2 – Resilient Client & Concurrency Prep

**Happy Path (Critical)**
- Enhance `reddit_client.py` with Tenacity-style retries/backoff and basic rate-limit handling (429 detection, structured exceptions).
- Ensure all orchestrator calls go through the resilient client and catch `FetchError` / `RateLimitError` without crashing runs.
- Introduce a small thread pool (or staged hook) so multiple queries can fetch concurrently, but keep pool size conservative to respect rate limits.
- Re-run preview/eval scripts to verify stability and measure runtime improvement.

**Extras (If Time)**
- Add telemetry hooks (e.g., counters for retries, rate-limit sleeps).
- Experiment with async HTTP client scaffolding (proof of concept only).

**Deliverable**
- Fetcher that survives transient API failures, respects rate limits, and has a clear path to faster runs (with basic concurrency in place or ready to toggle).

---

## Day 3 – Analyzer & Synthesis Demo

**Happy Path (Critical)**
- Build a lightweight analyzer script that loads eval/preview JSON and prints key metrics (query count, accepted posts, median karma, zero-comment drops, top queries).
- Freeze a dataset snapshot using the refactored fetcher and analyzer.
- Implement or finalize the synthesis step (prompt template + run script) that consumes the snapshot and outputs a demo-ready summary for at least one query.
- Produce sample outputs/screenshots for the portfolio.

**Extras (If Time)**
- Add CSV export or Markdown report to the analyzer.
- Run multiple synthesis variants to compare prompts.

**Deliverable**
- Analyzer output + synthesis results that showcase the end-to-end pipeline (fetch → analyze → summarize).

---

## Day 4 – Buffer & Portfolio Polish

**Happy Path (Critical)**
- Fix any bugs/regressions discovered during Day 3.
- Record or script the demo walkthrough (commands, expected outputs).
- Update README/portfolio notes with the final architecture, eval metrics, and synthesis summary.

**Extras (If Time)**
- Add optional CLI flags (e.g., for concurrency level) now that everything is stable.
- Write a short “lessons learned” or “future work” section to accompany the portfolio.

**Deliverable**
- Final repo state ready for submission: refactored fetcher, analyzer metrics, synthesis demo, and clear documentation describing how to run it all.

---
