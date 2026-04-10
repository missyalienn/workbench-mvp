# Design Doc: Batch Embedding for Semantic Ranking

## 1. Overview

Replaces the per-candidate serial embedding loop in `rank_candidates` with a single batched
API call. The OpenAI embeddings endpoint accepts a list of inputs and returns an ordered
response — we are not currently using that capability. Expected improvement: ranking latency
from ~10s to ~1s.

Tracking issue: #114

---

## 2. Problem

`rank_candidates` calls `get_or_create_embedding` once per candidate in a serial loop. With
45 candidates, this is up to 45 API round trips on a cold cache. The OpenAI embeddings API
accepts multiple inputs in a single request. We are not using it.

---

## 3. Design Goals

1. Replace the per-item embedding loop with a single batched API call per chunk.
2. Preserve per-item resilience — one bad input or one failed chunk must not zero-score
   all other candidates.
3. Validate and sanitize inputs locally before any API call.
4. Stay within documented API limits: ≤2048 inputs per request, ≤8192 tokens per input,
   ≤300,000 tokens total per request.
5. Reuse the existing retry policy — no new retry configuration or settings.
6. Keep log noise under control — one warning per chunk failure, not one per affected item.
7. No changes to `VectorStore` interface, cache schema, `RankingInput`, or downstream DTOs.

Non-goals:
- TTL or eviction for the embedding cache
- Parallel chunk dispatch
- Changes to the query embedding path (`embed_query`)

---

## 4. API Constraints (OpenAI Embeddings)

- `input` accepts a string or array of strings
- Max 2048 inputs per request
- Max 8192 tokens per individual input
- Max 300,000 tokens total across all inputs in one request
- Response includes an `index` field per embedding object for order-safe result mapping

Token estimation: `len(text) / 4` used as a conservative proxy. No external tokenizer
required.

---

## 5. Function Inventory

### Current

| Function | Location | Notes |
|---|---|---|
| `_fetch_embedding(*, client, model, text)` | `client.py` | Private, single API call |
| `EmbeddingClient.get_or_create_embedding(text)` | `client.py` | Cache + single API call |

### Proposed

| Function | Location | Change |
|---|---|---|
| `_fetch_embedding(*, client, model, text)` | `client.py` | Unchanged |
| `_fetch_embeddings(*, client, model, texts)` | `client.py` | New — batch API call |
| `EmbeddingClient.embed(text)` | `client.py` | Rename from `get_or_create_embedding` |
| `EmbeddingClient.embed_texts(texts)` | `client.py` | New — batch cache + API |

`embed` and `embed_texts` are a parallel pair. `embed` is used exclusively by `embed_query`
(single query embedding per run). `embed_texts` is used by `rank_candidates` (all
candidates).

### Callers updated

| Location | Current call | Updated call |
|---|---|---|
| `services/embedding/ranking.py:58` | `embedder.get_or_create_embedding(query)` | `embedder.embed(query)` |
| `services/embedding/ranking.py:77` | `embedder.get_or_create_embedding(post_text)` | removed — replaced by `embed_texts` |
| `tests/services/embedding/test_client.py` | `embedder.get_or_create_embedding(...)` | `embedder.embed(...)` |
| `tests/services/embedding/test_ranking.py` | `DummyEmbedder.get_or_create_embedding` | `DummyEmbedder.embed` |
| `services/embedding/client.py` docstring | example uses old name | updated |
| `docs/notes/todo.md` | references old name | updated |
| `docs/notes/http-retry-refactor.md` | references old name | updated |

---

## 6. Retry Policy

No new policy. `_fetch_embeddings` is decorated with the existing `_embedding_retry`,
built via `build_retry(is_retryable=_is_retryable_openai)`:

- Retryable: `RateLimitError`, `APITimeoutError`, `APIConnectionError`, `InternalServerError`
- Stop: `settings.RETRY_MAX_ATTEMPTS` (default 3)
- Wait: `wait_random_exponential(multiplier=settings.RETRY_WAIT_MULTIPLIER, max=settings.RETRY_WAIT_MAX)`
- After each attempt: warning via tenacity `after_log` (existing behavior)

Random exponential backoff is the documented OpenAI mitigation for rate limit errors. Failed
requests still count against RPM/TPM — the bounded attempt count and backoff together
prevent compounding the problem.

Retry is applied at the **chunk level**. A chunk that exhausts retries logs one warning and
marks its items as `None`. Other chunks are unaffected.

---

## 7. `embed_texts` Design

### Signature

```python
def embed_texts(self, texts: list[str]) -> list[list[float] | None]:
```

Returns a list parallel to `texts`. Each element is either the embedding vector or `None`
if that input was invalid or its chunk failed after retries. No `dims` returned — all
vectors from the same model have identical dimensionality, so it carries no value here.

### Steps

1. **Normalize** — apply `normalize_text` to every input.
2. **Validate** — any text that is empty after normalization is marked `None` immediately.
   Log `logger.warning("embedding.batch_input_invalid")` per bad input. In practice this
   will not fire for post candidates — the fetch pipeline filters them upstream — but the
   guard is correct for a general-purpose method.
3. **Cache lookup** — for each valid input, compute `content_digest` and check the store.
   Hits populate the result directly.
4. **Chunk misses** — collect miss indices. Build chunks greedily: add inputs until the
   next would exceed 2048 inputs or push the estimated token total past 300,000.
5. **Batch API call per chunk** — call `_fetch_embeddings` (decorated with
   `_embedding_retry`). If a chunk exhausts retries, log one
   `logger.warning("embedding.chunk_failed", n_affected=..., chunk_index=..., error=...)`
   and mark all items in that chunk as `None`. Continue with remaining chunks.
6. **Map results** — use the `index` field in each response object to map back to the
   original position within the chunk, then to the full result list.
7. **Cache write** — write each successful result to the store immediately after its chunk
   returns.
8. **Return** — ordered list parallel to input `texts`.

---

## 8. Changes to `rank_candidates`

**Current:** serial loop, one `embed` call per candidate.

**New:**
1. Build all post texts upfront (same truncation logic as today).
2. Call `embed_texts` once.
3. Zip candidates with results. `None` → `score=0.0`. Otherwise cosine similarity as today.

Per-item `score=0.0` fallback is preserved. Blast radius of a chunk failure is bounded to
candidates in that chunk. With 45 candidates at ~500 chars each, all misses fit in a single
chunk in practice — chunking is implemented correctly regardless.

---

## 9. Logging

| Event | Level | When |
|---|---|---|
| `embedding.batch_input_invalid` | WARNING | Input empty after normalization (one per bad input) |
| `embedding.chunk_failed` | WARNING | Chunk exhausts retries — includes `n_affected`, `chunk_index`, `error` |
| Per-item detail inside a failed chunk | — | Not logged (covered by chunk warning) |
| Tenacity retry attempts | WARNING | Via `after_log` in `build_retry` (existing behavior) |

---

## 10. Failure Modes

| Scenario | Behavior |
|---|---|
| Input empty after normalization | `None` for that item, one warning, others unaffected |
| Chunk fails after retries | `None` for all items in that chunk, one warning with count, other chunks unaffected |
| All chunks fail | All posts get `score=0.0`, existing `fetch.ranking_fallback` warning fires at caller |
| Cache read fails | Falls through to API call (existing cache behavior) |
| Cache write fails | Logged at WARNING by cache module, result still returned (existing behavior) |

---

## 11. Files Changed

| File | Change |
|---|---|
| `services/embedding/client.py` | Rename `get_or_create_embedding` → `embed`; add `_fetch_embeddings`, `embed_texts` |
| `services/embedding/ranking.py` | Update `embed_query` caller; replace loop in `rank_candidates` with `embed_texts` |
| `tests/services/embedding/test_client.py` | Rename existing test; add `embed_texts` tests |
| `tests/services/embedding/test_ranking.py` | Update `DummyEmbedder`; update affected tests |
| `docs/notes/todo.md` | Update stale function name references |
| `docs/notes/http-retry-refactor.md` | Update stale function name references |

No changes to: `store.py`, `cache.py`, `sqlite_store.py`, `store_factory.py`,
`similarity.py`, `retry_policy.py`, `settings.py`, or any downstream DTOs.

---

## 12. Testing

**`test_client.py`** — new tests for `embed_texts`:
- All inputs hit cache — no API call made
- All inputs miss cache — one batch API call, results cached and returned
- Mixed hits and misses — only misses sent to API
- Empty input after normalization — `None` for that index, others unaffected
- Chunk fails after retries — `None` for chunk items, others unaffected

**`test_ranking.py`** — updates:
- `DummyEmbedder.get_or_create_embedding` → `embed`
- Add `DummyEmbedder.embed_texts`
- `test_rank_candidates_scoring` — updated to batch path
- `test_rank_candidates_post_embedding_failure` — failure is now `None` returned for a
  specific item, that post gets `score=0.0`, others unaffected
