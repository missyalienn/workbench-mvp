# 0003 — Source-agnostic Loaders; planner retired

**Status:** Accepted (2026-10-19)

**Context:** V1 is Reddit-coupled end to end (`Post`, `Comment`, `SearchPlan`). V2 must accept new sources without changes outside the source's own module.

**Decision:**
- Each source is a `Loader` (LangChain `BaseLoader`) emitting canonical `Document`s via `crawl(scope)` and `fetch(query)`.
- Splitting, embedding, indexing, retrieval are shared and source-unaware.
- Reddit: one thread (title + body + top filtered comments) = one `Document`. Reddit types never leave the Reddit loader.
- V1 planner retired; loaders translate plain-language queries into source-specific search (e.g. subreddit selection).

**Consequences:**
- Adding a source = one new loader + config.
- V1 filtering logic is reused inside the Reddit loader, copied not imported.
