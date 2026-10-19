# 0002 — Pinecone: one index per embedding model, one namespace

**Status:** Accepted (2026-10-19)

**Context:** V2 needs a persistent index usable from any host. Vectors from different embedding models are not comparable.

**Decision:**
- Pinecone, single index, single namespace; filter by `metadata.source`.
- Index name encodes the embedding model, e.g. `workbench-oai-te3s-1536` (`text-embedding-3-small`).
- Embedding model swap = new index → re-run ingestion → change `PINECONE_INDEX` setting.
- Plain similarity retrieval; add a reranker only if evals show misses. Store source quality signal in metadata.

**Consequences:**
- Cross-source search is one query.
- Old index remains for rollback until manually retired.
- Per-source deletion via metadata filter.
