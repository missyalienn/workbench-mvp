# 0001 — Adopt LangChain v1 + LangGraph; model-agnostic

**Status:** Accepted (2026-10-19)

**Context:** V2 needs an agent, retrieval, multi-turn state, and provider swaps without rewrites. The abandoned POC banned LangChain abstractions; V1 calls the OpenAI Responses API directly.

**Decision:**
- Use LangChain v1 standard components (`Document`, `BaseLoader`, text splitters, `PineconeVectorStore`, retrievers) and `create_agent` (built on LangGraph).
- Chat model via `init_chat_model` from settings; embeddings via `init_embeddings`. OpenAI for now.
- No provider-specific features (e.g. Responses API structured output) in app code.

**Consequences:**
- Supersedes the POC's no-LangChain rule.
- Swapping chat provider is a settings change; swapping embeddings requires re-ingestion (see 0002).
- Custom code limited to loaders, tools, prompts, middleware, evals.
