# Semantic Ranking v1 — Implementation Plan

Mentor voice, step-by-step, no code, smallest safe slice first.

## Step 1 — Config Flags

- Add config flags and defaults (`USE_SEMANTIC_RANKING`, `EMBEDDING_MODEL`, `EMBEDDING_CACHE_PATH`, `MAX_EMBED_TEXT_CHARS`) without changing behavior.
- This gives you a safe toggle and keeps the current pipeline stable.

## Step 2 — Embedding Cache

- Create the embedding cache module with the SQLite schema and connection settings (WAL, busy_timeout, per-operation connections).
- Don't wire it yet; just make sure it can read/write idempotently.

## Step 3 — Embedding Client

- Create the embedding client module that normalizes text, computes a digest, checks cache, calls the embeddings API on a miss, and stores results.
- Wrap the API call with Tenacity and return a vector; keep the client local (no globals).

## Step 4 — Similarity Helper

- Implement the cosine similarity helper with vector normalization and zero-norm safety.
- This stays isolated so scoring logic is clean and testable.

## Step 5 — Two-Phase Fetcher

- Refactor the fetcher into two internal phases without changing outputs.
- Phase A fetches posts, validates, fetches comments, and builds `Post` objects.
- Phase B scores the built posts.
- With the flag off, Phase B should still use keyword scoring so behavior is unchanged.
- Place the phase split in `services/fetch/reddit_fetcher.py` by separating scoring from `_fetch_posts_for_pair` (Phase A) and applying Phase B after posts are built, before returning from `run_reddit_fetcher`.

## Step 6 — Query Embedding

- Add query embedding in Phase B: compute it once per fetch run, use cache if present, and on failure default the query vector to "missing" so posts can be scored as 0.0.
- This keeps the system running even if embeddings fail.

## Step 7 — Post Embedding and Scoring

- Add post embedding + semantic scoring in Phase B.
- For each built post, embed `title + "\n\n" + body`, truncate to `MAX_EMBED_TEXT_CHARS`, and compute cosine similarity with the query vector.
- Assign that to `relevance_score`.
- If embedding fails, set `relevance_score = 0.0`.

## Step 8 — Feature Flag Wiring

- Wire the feature flag: if `USE_SEMANTIC_RANKING` is true, use semantic scoring and set `matched_keywords = []`.
- If false, keep keyword scoring exactly as before.
- This preserves rollback safety.
- Dev policy: do not fall back to keyword scoring; semantic must run successfully to proceed in dev.

## Step 9 — Focused Tests

- Add focused tests: cache read/write idempotency, semantic ranking changes ordering, and embedding failure results in karma-only ordering (all scores 0.0).
- Also add a regression test that the two-phase fetcher returns the same DTO shapes.

## Step 10 — Dev Validation

- Validate in dev: run once with the flag off to confirm zero regressions, then on to confirm cache creation and ranking shifts.
- If anything breaks, flip the flag back and re-run to verify immediate rollback.

## Baseline Evaluation Note

- Use existing runs in `data/pipeline_stage_summaries/` and `data/evidence_previews/` as the before baseline, then compare top-N ordering after semantic ranking is enabled.

## Risk Checklist

- Separation of concerns: fetching/building posts and scoring are in separate phases.
- No global clients: embedding client is created within the scoring path.
- Idempotent embeddings: same text + model yields the same cached vector.
- Failure handling: embedding failures result in `relevance_score = 0.0`, not pipeline failure.
- Rollback safety: feature flag restores keyword scoring without DTO or selector changes.
- Concurrency safety: SQLite cache uses per-operation connections, WAL, and busy_timeout.
- Dev gating: if semantic scoring is unavailable and no cached embeddings exist, fail fast rather than using keyword scoring.

## Dev Validation

- Do not allow keyword fallback in dev; semantic must succeed or the run fails.
- If embeddings fail and no cache exists, fail fast instead of degrading to keyword.
- Accept semantic as the new baseline if it is not worse than keyword on existing runs.
- Use `data/pipeline_stage_summaries/` and `data/evidence_previews/` to compare top-N quality before and after.
- Use `docs/notes/concurrency_results.md` as the fetch-latency baseline; expect first run slower and subsequent runs faster after cache warm-up.

## Pre-Flight Checklist

- Cache key normalization is consistent so digests match across runs.
- Embedding model and `dims` are validated to avoid mismatched vectors.
- Text truncation is applied deterministically before embedding.
- Scoring happens after validation and duplicate filtering to avoid wasted embeddings.
- Failure paths keep posts (score = 0.0) rather than dropping them.
- Two-phase refactor keeps the post set identical when the flag is off.
