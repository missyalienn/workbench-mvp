# Manual Smoke Tests

Quick, human-triggered checks we run when wiring new features or tuning the planner/fetcher stack. Each section explains why the test exists, how to launch it, and what to look for. See `docs/reddit_fetcher_baselines.md` for detailed acceptance metrics.

## Planner Smoke Test
- **Script:** `scripts/planner_smoke_test.py`
- **Purpose:** Fast sanity check that the planner can turn a handful of DIY queries into SearchPlans without raising errors.
- **Command:**
  ```bash
  python -m scripts.planner_smoke_test "How do I hang floating shelves?"
  ```
  (Omit arguments to use the default query list baked into the script.)
- **Expected Output:** Logs showing each query, the returned `plan.query`, and the lists of search_terms/subreddits/notes. Failures surface as logged errors for immediate debugging.
- **Tip:** Use `python -m scripts.save_plan "How do I hang floating shelves?"` when you want to persist a planner output to JSON for later fetcher testing. Files land in `data/plans/` with slugged names.

## Reddit Fetcher Smoke Test
- **Script:** `scripts/reddit_fetcher_smoke_test.py` (to be implemented per requirements)
- **Purpose:** Execute the full fetcher pipeline against a real planner-produced SearchPlan. Validates transport, validation, scoring, and comment nesting in one go.
- **Command:**
  ```bash
  python scripts/reddit_fetcher_smoke_test.py --plan-path data/sample_plan.json --post-limit 5
  ```
  (Load a serialized SearchPlan captured from the planner smoke test or baseline run.)
- **Expected Output:** Structured logs showing the number of candidates fetched, rejection reasons, and accepted posts/comments. Review the emitted FetchResult to confirm URLs, scores, and comments look healthy. For acceptance-rate targets, see `docs/reddit_fetcher_baselines.md`.
- **Requirements Recap:** Use a real SearchPlan, respect rate limits (`restrict_sr=1`, `include_over_18=false`), log counts (posts accepted, comments accepted), and avoid `print` statements—stick to the shared logger.

## Planner Baseline Evaluation
- **Script:** `scripts/baseline_eval.py`
- **Purpose:** Regression sweep across a fixed set of novice DIY queries to catch planner drift. Generates JSONL output for diffing across runs.
- **Command:**
  ```bash
  python scripts/baseline_eval.py
  ```
- **Expected Output:**
  - Logs summarizing how many plans were valid.
  - A file under `logs/baseline_eval_<timestamp>.jsonl` containing per-query runtime, validity, plan_id, and any validation errors. Useful for historical comparisons. 
