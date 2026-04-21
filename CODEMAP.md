# CODEMAP — workbench-mvp
_One line per non-trivial file. Update when files are added or renamed. Skip __init__.py._

## api/
- `app.py` — FastAPI app, route registration
- `errors.py` — exception handlers, HTTP error mapping
- `pipeline.py` — wires all 5 pipeline stages; main execution path

## agent/
- `clients/openai_client.py` — OpenAI API client wrapper
- `planner/core.py` — turns query into structured SearchPlan
- `planner/model.py` — SearchPlan and related types
- `planner/prompt_templates.py` — prompts for planner LLM call

## common/
- `exceptions.py` — shared exception types

## config/
- `settings.py` — Pydantic settings, all env vars; source of truth for config
- `logging_config.py` — structlog setup; get_logger(), plan_context_scope()

## graph/
- `schemas.py` — graph data schemas
- `tools/dob_tool.py` — Department of Buildings data tool
- `tools/permit_client.py` — permit data client
- `tools/reddit.py` — Reddit tool for graph agent

## services/context_builder/
- `config.py` — token budget and selection config

## services/embedding/
- `client.py` — OpenAI embeddings client
- `cache.py` — SQLite embedding cache
- `ranking.py` — cosine similarity scoring; karma sort fallback
- `similarity.py` — similarity computation
- `store.py` — embedding store interface (ABC)
- `store_factory.py` — factory for store instantiation
- `stores/sqlite_store.py` — SQLite store implementation

## services/fetch/
- `reddit_fetcher.py` — main fetcher; orchestrates fetch pipeline
- `schemas.py` — PostCandidate, Post, FetchResult types
- `reddit_builders.py` — builds Post objects from raw Reddit data
- `reddit_validation.py` — validates raw Reddit API responses
- `comment_pipeline.py` — comment fetching and processing
- `content_filters.py` — content filtering logic
- `scoring.py` — post scoring
- `keyword_groups.py` — keyword grouping for search
- `utils/datetime_utils.py` — datetime helpers
- `utils/text_utils.py` — text processing helpers

## services/http/
- `retry_policy.py` — generic build_retry(is_retryable) factory

## services/reddit_client/
- `client.py` — Reddit API client
- `endpoints.py` — Reddit API endpoint definitions
- `session.py` — HTTP session with auth

## services/synthesizer/
- `models.py` — EvidenceResult, EvidenceRequest; core output types
- `context_builder.py` — builds synthesis context from ranked evidence
- `config.py` — synthesizer config
- `stage_summary.py` — stage summary for observability
- `llm_execution/llm_client.py` — executes LLM API call
- `llm_execution/prompt_builder.py` — builds synthesis prompt
- `llm_execution/types.py` — LLM execution types

## scripts/
- `runs/` — dev/demo run scripts; not production code
- `smoke/` — smoke tests and manual validation scripts

## tests/
Mirrors src structure. Run with `pytest`.
