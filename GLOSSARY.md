# Glossary

V2 (`app/`) terminology. V1 terms (`Post`, `EvidenceResult`, `ThreadEvidence`, `SearchPlan`) are legacy and not used in V2.

| Term | Definition | Avoid |
|---|---|---|
| **Source** | An external content provider (e.g. Reddit). Stored as `metadata.source` on every `Document`. | platform, provider |
| **Loader** | Adapter for one source; implements LangChain `BaseLoader`. Emits `Document`s via `crawl(scope)` (ingestion) and `fetch(query)` (live). | fetcher, client, source adapter |
| **Document** | LangChain `Document`: `page_content` + `metadata`. One unit of source content (a Reddit thread = one Document). | post, item |
| **Chunk** | A `Document` produced by splitting a parent Document for indexing. Carries `metadata.parent_id`. | snippet, passage |
| **Index** | The Pinecone index holding chunk embeddings. Named after its embedding model. | corpus, store |
| **Ingestion** | Batch job: Loader → split → embed → upsert into the index. | crawl job, sync |
| **Write-through** | Background indexing of `fetch_live` results after a turn. | cache fill |
| **Purge** | Job deleting expired or source-deleted chunks from the index. | cleanup, retention job |
| **Retriever** | LangChain `Retriever` over the index; exposed to the agent as the `search_index` tool. | searcher, ranker |
| **Tool** | A function the agent may call (`search_index`, `fetch_live`). | action, skill |
| **Agent** | The `create_agent` tool-calling loop that answers a turn. | assistant, bot |
| **Middleware** | `create_agent` hooks for cross-cutting behavior: limits, guardrail, summarization. | plugin |
| **Guardrail** | Middleware rejecting off-domain (non-DIY) requests. | filter |
| **Thread** | A conversation, identified by `thread_id`. Owner `user_id` is nullable (anonymous). | session, chat |
| **Turn** | One `HumanMessage` and the agent's resulting messages, ending in an `AIMessage`. | request, exchange |
| **Checkpointer** | LangGraph persistence for thread state (`PostgresSaver` on Supabase). | memory store |
| **Citation** | Structured reference to a chunk used in an answer: `document_id`, `url`, `source`, `title`, `snippet`. | evidence, reference |
| **Eval** | A LangSmith experiment scoring the agent on the dataset. | benchmark, test |
| **Baseline** | The accepted eval scores that later changes must not regress below. | target |
