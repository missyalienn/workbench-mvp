# Design Doc: Semantic Ranking v1 

## 1. Overview

This refactor replaces keyword-based ranking with semantic similarity ranking using OpenAI embeddings.

The goal is to decouple ranking from brittle keyword heuristics while:

* Minimizing changes to existing DTOs and selection logic
* Allowing a small, internal fetcher restructure to isolate scoring
* Preserving rollback capability
* Maintaining graceful degradation when embeddings fail

This is a scoring-layer refactor with a two-phase fetcher, not a new pipeline or external contract.


## 2. Current Architecture (Relevant Parts)

### Fetcher

* Fetches posts per (subreddit, term)
* Applies validation filters (NSFW, length, duplicates, etc.)
* Fetches comments
* Builds `Post` model
* Assigns `relevance_score` via `evaluate_post_relevance`

### Selector

* Sorts posts by:

  1. `relevance_score`
  2. `post_karma`
* Truncates to `cfg.max_posts`
* Builds `PostPayload`

### Key Constraint

`PostPayload` and `Post` DTOs currently contain:

* `relevance_score`
* `matched_keywords`

Selection and downstream LLM logic depend only on `relevance_score`, not how it was computed.


## 3. Design Goals

1. Replace keyword ranking with semantic similarity ranking.
2. Do not rename DTO fields.
3. Keep comment fetching order unchanged (comments still fetched before scoring).
4. Do not modify selector logic.
5. Remove keyword logic from main ranking path.
6. Allow instant rollback via config flag.
7. Degrade to karma-only sorting if embeddings fail.
8. Use a vector store abstraction for embeddings (SQLite implementation in v1).
9. Isolate scoring into a second internal phase (fetch/build first, score second).

Non-goals (v1):

* Rank-before-comments optimization
* Keyword fallback scoring
* Vector database
* TTL/eviction for cache
* Schema redesign

## 4. High-Level Architecture

### 4.1 Fetcher Phases

Phase A (unchanged behavior):

* Fetch posts per (subreddit, term)
* Apply validation filters
* Fetch comments
* Build `Post` objects

Phase B (new internal phase):

* Compute `relevance_score` for each built post
* Semantic scoring when enabled; keyword scoring remains as a rollback path

External interfaces and DTO shapes remain unchanged.

### 4.2 Scoring Model

`relevance_score` becomes:

> Fetcher-assigned ranking score (semantic similarity)

Keyword scoring is no longer used in semantic mode.

Selector remains unchanged.

## 5. Semantic Ranking Flow

### 5.1 Query Embedding

* Compute embedding for `plan.query` once per fetch run.
* Use cache if available.
* If embedding fails and no cached value exists:

  * All posts default to `relevance_score = 0.0`.

### 5.2 Post Embedding

For each post:

* Build candidate text: `title + "\n\n" + body`
* Truncate to `MAX_EMBED_TEXT_CHARS`
* Retrieve embedding from cache OR compute via API
* If embedding fails:

  * Assign `relevance_score = 0.0`
* Otherwise:

  * Compute cosine similarity(query_vec, post_vec)
  * Assign that value to `relevance_score`

Embedding requests may be batched internally for performance, but the scoring outcome is identical.

### 5.3 Selection

Unchanged:

* Sort by `relevance_score`
* Break ties by `post_karma`
* Truncate to `cfg.max_posts`


## 6. Failure Modes

### 6.1 Embedding API Down (First Run)

* No cached embeddings
* All posts get `relevance_score = 0.0`
* Selector sorts by karma

Pipeline continues.

### 6.2 Embedding API Down (Subsequent Runs)

* Cached embeddings used where available
* Only new posts degrade to `0.0`
* Partial semantic ranking preserved

### 6.3 SQLite Issues

* If cache DB fails:

  * Log error
  * Proceed without caching
  * Still attempt API calls

No hard system failure.

## 7. SQLite Embedding Cache

## 7. Vector Store Abstraction

Semantic ranking depends on a small vector-store interface, not a specific backend.

### 7.1 Interface (v1)

* `get_embedding(digest, model) -> (vector, dims) | None`
* `set_embedding(digest, model, dims, vector) -> None`

### 7.2 SQLite Implementation (v1)

SQLite is the initial backend, but it is not the contract.

#### Table Schema

Single table:

* content_digest (TEXT)
* model (TEXT)
* dims (INTEGER)
* embedding (BLOB)
* PRIMARY KEY (content_digest, model)

#### Storage Format

* Embeddings stored as BLOB (float32)
* No JSON storage
* No TTL
* No eviction

#### Concurrency

* Per-operation connection
* WAL mode enabled
* busy_timeout configured
* No shared connection object


## 8. Configuration

New settings:

* `USE_SEMANTIC_RANKING` (bool)
* `EMBEDDING_MODEL`
* `VECTOR_STORE_TYPE` (e.g., `sqlite`)
* `EMBEDDING_CACHE_PATH` (SQLite only)
* `MAX_EMBED_TEXT_CHARS`

Rollback strategy:

* Set `USE_SEMANTIC_RANKING = False`
* System reverts to keyword scoring immediately


## 9. Rollback Plan

Rollback requires:

* No schema renames
* No DTO renames
* No selector modifications
* Keyword logic preserved in codebase

To revert:

* Flip feature flag
* Redeploy

No migration required.


## 10. Testing Strategy

Minimum validation:

1. Semantic ranking changes ordering vs keyword ranking.
2. First-run cache creation works.
3. Subsequent run hits cache.
4. Embedding failure results in karma-only ordering.
5. Feature flag restores keyword behavior exactly.

## 11. Future Iterations (Not v1)

* Rank-before-comments optimization
* Remove keyword code entirely
* Rename `relevance_score` → `semantic_score`
* Add score_source field
* Add non-SQLite vector store (Pinecone or similar)


## Sanity Check

This design:

* Minimizes churn
* Minimizes surface area
* Preserves rollback
* Removes keyword dependency from ranking
* Keeps selector untouched
* Keeps DTO untouched
* Adds isolated semantic layer
