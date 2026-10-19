# 0007 — Live fetch write-through and purge

**Status:** Accepted (2026-10-19)

**Context:** The agent calls `fetch_live` when the index lacks coverage. Persisting third-party content carries retention obligations.

**Decision:**
- `fetch_live` results are upserted after the turn as a background task.
- Deterministic chunk IDs (`<source>:<native_id>:<chunk_n>`) make re-indexing idempotent.
- Every chunk stamped with `source` and `fetched_at` from day one.
- Each loader declares its retention policy; a shared purge job deletes expired or source-deleted chunks.

**Consequences:**
- Index grows where users ask.
- Purge job is required before cutover, not before.
