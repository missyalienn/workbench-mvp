# 0004 — Supabase checkpointer; anonymous threads

**Status:** Accepted (2026-10-19)

**Context:** Multi-turn conversation needs persisted thread state. No user accounts exist; minimal infra ops desired.

**Decision:**
- LangGraph `PostgresSaver` on Supabase Postgres (free tier); separate dev and prod projects. No local Postgres container.
- Threads anonymous: browser holds `thread_id`; `user_id` nullable from day one.
- Anonymous threads expire after a TTL (setting). Long threads summarized via middleware.

**Consequences:**
- Local dev requires network access to Supabase dev project.
- Supabase Auth is the natural path when `user_id` becomes real.
