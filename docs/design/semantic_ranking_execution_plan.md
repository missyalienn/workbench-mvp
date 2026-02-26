# Semantic Ranking v1 — Change-Scope Execution Plan 
---

## 1. Goals & Constraints

### Goals

* Replace keyword-based ranking with semantic similarity ranking.
* Decouple ranking logic from brittle keyword heuristics.
* Preserve selector and DTO behavior.
* Maintain graceful degradation (karma-only).
* Allow instant rollback.
* Isolate scoring into a second internal phase (fetch/build first, score second).

### Constraints

* No DTO renames.
* No selector rewrite.
* No rank-before-comments refactor.
* No external contract changes.
* Must be rollback-safe via feature flag.
* Must support concurrency (3 workers).
* Must use SQLite cache (stdlib only).

---

## 2. What Stays Exactly the Same

### Unchanged Modules

* `SelectorConfig`
* `select_posts`
* `build_post_payload`
* `build_summarize_request`
* `PostPayload` DTO shape
* `FetchResult`
* Comment filtering logic
* Validation logic (NSFW, too short, duplicate, etc.)
* Concurrency structure
* Tenacity retry behavior
* Rate limiting behavior

### Unchanged Behavior

* Selector sorts by:

  1. `relevance_score`
  2. `post_karma`
* Selector truncates to `cfg.max_posts`
* Comments fetched before scoring
* Post and comment DTO structure

No external contract changes.

---

## 3. What Changes 

### 3.1 Ranking Algorithm

Replace:

* `evaluate_post_relevance()` keyword scoring

With:

* Semantic similarity scoring (embedding + cosine)

`relevance_score` remains the field used for ranking.

Its meaning changes from:

> keyword weighting score

To:

> semantic similarity score

No field rename.

---

### 3.2 Fetcher Internal Structure

Refactor the fetcher into two internal phases:

* Phase A: fetch posts, apply validation filters, fetch comments, build `Post` objects
* Phase B: compute `relevance_score` for each built post

No change to the external fetcher interface or DTO outputs.

### 3.3 Scoring Switch

Add a feature flag:

* `USE_SEMANTIC_RANKING: bool`

If `False`:

* Use existing keyword scoring unchanged.

If `True`:

* Use semantic scoring and set `matched_keywords=[]`.

Rollback = flip flag.

### 3.4 Add New Modules (Isolated Additions)

New directory:

* `services/embedding/`

Files:

* `cache.py`
* `client.py`
* `similarity.py`

These are additive. They do not modify existing modules beyond being called.

## 4. New Components (Additive Only)

### 4.1 Embedding Cache (SQLite)

Single table:

* content_digest
* model
* dims
* embedding (BLOB)
* primary key: (content_digest, model)

No migrations.
No eviction.
No TTL.

Thread-safe via:

* Per-operation connections
* WAL mode
* busy_timeout


### 4.2 Embedding Client

Responsibilities:

* Normalize text
* Hash digest
* Check cache
* Call OpenAI API if needed
* Store embedding in cache
* Return numpy vector

Failure behavior:

* Raise controlled exception
* Caller decides fallback (assign 0.0)


### 4.3 Similarity Function

* Cosine similarity using numpy
* Normalize vectors
* Safe for zero-norm vectors

Returns float score.

## 5. Failure & Degradation Behavior

### Case 1 — Embeddings API works

* Full semantic ranking
* Cache warms

### Case 2 — API partially fails

* Cached embeddings used
* Failed posts receive `relevance_score = 0.0`
* Karma breaks ties

### Case 3 — API fully fails (no cache)

* All posts receive `relevance_score = 0.0`
* Selector sorts by karma only

System continues.

No keyword fallback.

## 6. Rollback Strategy

Rollback requires:

* Do not remove keyword scoring code.
* Do not rename `relevance_score`.
* Do not alter selector behavior.
* Do not alter DTO shapes.

To revert:

* Set `USE_SEMANTIC_RANKING = False`

System returns to previous behavior instantly.

No schema migration.
No downstream changes.

## 7. Risk Surface

### Low Risk

* DTO stability
* Selector stability
* FetchResult stability

### Moderate Risk

* Embedding latency
* SQLite locking (mitigated by WAL + per-op connection)
* Scoring phase integration (internal only)

### High Risk (Operational Only)

* OpenAI API outage
  → mitigated by karma fallback

No structural risk.

## 8. Testing Checklist

### Before Enabling Semantic

* Confirm keyword ranking still works with flag off.
* Confirm two-phase fetcher returns the same posts and DTO shapes.

### With Semantic Enabled

* Confirm cache file is created.
* Confirm embeddings stored.
* Confirm semantic ranking changes ordering.
* Simulate API failure → confirm karma-only fallback.
* Flip flag → confirm keyword ranking restored.

## 9. Future Iterations (Out of Scope)

* Rank-before-comments optimization
* Remove keyword code entirely
* Rename `relevance_score`
* Introduce `score_source`
* Introduce vector DB
* Add cache eviction
