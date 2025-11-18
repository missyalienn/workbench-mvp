## Minimal Multithreading Plan for the Reddit Fetcher

Goal: add a small, optional thread pool to run multiple `(subreddit, term)` fetches in parallel, plus a timing log to measure before/after. Keep it easy to turn off and easy to revert.

### Terminology
- We’ll call this **multithreading** (a thread pool with a few worker threads). It’s the simplest way to add concurrency without rewriting code to async/await.

### Step-by-Step
1) **Config knobs**  
   - Add `FETCHER_MAX_WORKERS` (start with 2–3).  
   - Add `FETCHER_ENABLE_CONCURRENCY` (default False so current behavior stays as-is).  
   - These live in `config/settings.py` and let us toggle the pool on/off without code edits.

2) **Timing log in the preview script**  
   - In `scripts/run_fetch_preview.py`, record `start = time.perf_counter()` before `run_reddit_fetcher(...)` and `end = time.perf_counter()` after.  
   - Log/print the elapsed seconds and the count of subreddits × terms. This gives a clean before/after number without relying on `/usr/bin/time`.

3) **Helper for one task**  
   - In `services/fetch/reddit_fetcher.py`, add a helper that processes one `(subreddit, term, post_limit, fetched_at)` and returns `list[Post]`.  
   - Inside the helper: create a fresh `RedditClient`, run the existing per-post logic (validation, scoring, fetch comments, build models), and return the accepted posts. Do not share `seen_post_ids` here.

4) **Thread pool wiring**  
   - In `run_reddit_fetcher`, build all `(subreddit, term)` tasks.  
   - If concurrency is disabled, run tasks serially (current behavior).  
   - If enabled, create `ThreadPoolExecutor(max_workers=settings.FETCHER_MAX_WORKERS)`, submit one task per pair, and gather futures with `as_completed`.  
   - Maintain a single `seen_post_ids` in the main thread; as each future returns `list[Post]`, skip any post whose ID is already seen, otherwise add it to the master `accepted_posts`.

5) **API stability / rollback**  
   - Keep `run_reddit_fetcher`’s signature the same; callers don’t change.  
   - Because it’s driven by config, turning concurrency off is just flipping the toggle. No risky rollback needed.

6) **Measure and decide**  
   - Run `scripts/run_fetch_preview.py` with concurrency off to capture baseline (timing log).  
   - Turn concurrency on (small worker count) and rerun the same queries; compare elapsed time.  
   - If gains are minimal, set the toggle back to False and you’re back to serial.

