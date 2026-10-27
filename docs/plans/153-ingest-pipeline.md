# Plan: #153 — Loader contract, Reddit loader, indexing pipeline, ingest CLI

## Context
Step 1 of 8 for V2 (ADRs 0002, 0003, 0007; `docs/design/architecture.md`). V2 needs a persistent, source-agnostic Pinecone index. Nothing exists under `app/` yet. V1 stays untouched: V1 code is **copied** into `app/`, never imported (acceptance criterion).

Decisions made with user: env-only Reddit credentials; `fetch()` is contract-only (`reddit.Loader.fetch` → `NotImplementedError`, built in #155); crawl scope = top listings + optional search queries; scope bound at loader construction.

## New dependencies (need approval; bare names, no invented bounds; audit after add)
`langchain` (for `init_embeddings`), `langchain-core`, `langchain-text-splitters`, `langchain-openai`, `langchain-pinecone`. Already present: httpx, tenacity, pydantic-settings, structlog, PyYAML, typer, markdown-it-py, beautifulsoup4. `keyring`/`boto3` are NOT carried into `app/`.

## Layout (new files)
```
app/__init__.py
app/config/{__init__,settings,logging_config}.py   # settings: env-only (REDDIT_*, OPENAI_API_KEY, PINECONE_*, EMBEDDING_MODEL, chunk size/overlap, retry, log)
app/common/{__init__,exceptions,retry_policy}.py   # copied from common/exceptions.py, services/http/retry_policy.py
app/loaders/{__init__,base}.py                     # Loader contract
app/loaders/reddit/{__init__,scope,client,filters,loader}.py
app/indexing/{__init__,ids,splitter,pipeline}.py
config/ingest_scope.yaml                           # reddit scope (subreddits, sort, time_filter, limit, queries)
scripts/ingest.py
tests/app/{loaders,indexing,scripts}/test_*.py     # unique basenames (tests/ has no __init__.py)
```
New pattern to flag: an `app/`-local copy of logging/retry/exceptions (design doc says "copied from V1"). Settings are a fresh `app/config/settings.py` so V1 `config.settings` (keychain/SSM/planner fields) is not dragged in.

## Components
**`loaders/base.py`** — `Loader(BaseLoader, ABC)`: `source: ClassVar[str]`; scope bound in `__init__`; `alazy_load()` is the crawl (`crawl()` thin alias); abstract `async fetch(query) -> list[Document]`; sync `lazy_load` unsupported (raises). Contract for emitted `Document.metadata`: `source`, `native_id`, `url`, `title`, `fetched_at` (epoch float, filterable for purge), `quality_score` (Reddit: post karma). Source-specific extras (e.g. `subreddit`) allowed; Pinecone-safe scalar types only.

**`loaders/reddit/`**
- **Naming (user decision):** the provider name lives only in the package path `app/loaders/reddit/`, env vars (`REDDIT_*`), YAML key (`reddit:`), and `metadata.source="reddit"` data. Identifiers inside use role names: `Loader`, `Client`, `Session`, `Scope`. `loader.py` does `from app.loaders import base` + `class Loader(base.Loader)`; callers use `from app.loaders import reddit` → `reddit.Loader`, `reddit.Scope`. The CLI maps `--loader reddit` → `reddit.Loader`. Glossary term "Reddit loader" still valid as prose.
- `scope.py`: pydantic `Scope` (subreddits, sort, time_filter, limit_per_subreddit, queries, max_comments); loaded from YAML, validated.
- `client.py`: copy of `services/reddit_client` session (env creds only, `AuthError` if missing), `search_subreddit`, `paginate_search`, `fetch_comments`, httpx→typed error translation; **add** one listing endpoint `/r/{sub}/{sort}` with `t=` and pagination. Retry predicate stays here.
- `filters.py`: copy of post validation (deleted, AutoModerator, ads, non-self, NSFW, showcase), `clean_text`, min post length 250, comment filters (dedup, AutoMod, deleted, karma ≥ 2, min length 140, top-N by karma). **Decision:** V1 keyword relevance scoring is *not* copied — crawl targets DIY subreddits and retrieval handles relevance; showcase phrases are inlined as a small tuple instead of importing `keyword_groups`.
- `loader.py`: `Loader.alazy_load`: per subreddit, listing + queries → dedupe by post id → validate/clean → fetch comments concurrently (semaphore-bounded) → drop threads with no surviving comments (V1 behaviour) → one `Document` per thread (`page_content` = title + body + "Top comments" list). Typed fetch failures logged (`loader.request_failed`) and skipped per-post/per-subreddit, not fatal for the whole crawl.

**`indexing/`**
- `ids.py`: `chunk_id(source, native_id, n) -> "<source>:<native_id>:<n>"`.
- `splitter.py`: `RecursiveCharacterTextSplitter` built from settings.
- `pipeline.py`: `index_documents(docs, *, vector_store)` → split → stamp `parent_id` (`<source>:<native_id>`), `chunk_n`, deterministic ids → `PineconeVectorStore.add_documents(ids=…, batch_size=…)`. Vector store built from `init_embeddings("openai:<EMBEDDING_MODEL>")` + `PINECONE_INDEX`; fails loudly if index doesn't exist (user creates `workbench-oai-te3s-1536` once — **open: auto-create?**). Re-ingest = same ids → upsert overwrites (idempotent). Known gap: if a thread shrinks, higher-`chunk_n` orphans remain → left to purge job (#160).

**`scripts/ingest.py`** (typer, matches existing scripts): `--loader reddit` (required), `--scope PATH` (default `config/ingest_scope.yaml`), `--dry-run` (load + split, no embed/upsert, prints counts). Pure args + exit codes: 0 success, 1 runtime failure (external service/index), 2 usage/config error. No prompts, no interactive output beyond structured logs. Loader name → factory via a plain dict (single case; no registry framework).

## Tests (no network; alongside the code)
- Reddit filters: each post/comment rule incl. boundaries (the V1 `# TODO: add tests` gaps).
- Loader mapping: stub client → Document content/metadata, thread dropped when no comments, per-request failure skipped.
- Client: listing pagination, retry predicate, error translation (follow `tests/services/reddit_client/test_endpoints.py` pattern with `AsyncMock(httpx.AsyncClient)`).
- Scope: YAML validation errors.
- Indexing: `chunk_id` format, parent_id/chunk_n/metadata stamped on every chunk, ids stable across two runs, `add_documents` called with ids (fake vector store).
- CLI: `typer.testing.CliRunner` — exit codes 0/1/2, `--dry-run` doesn't touch vector store, unknown `--loader` → 2.
- Optional `@pytest.mark.integration` Pinecone round-trip (skipped by default; register marker in `pytest.ini`).

## Execution order (one piece at a time, stop between)
1. Deps + `app/config` + `app/common` (+ tests for settings/retry)
2. `Loader` base + Reddit scope/client/filters (+ tests)
3. `reddit.Loader` (+ tests)
4. Indexing (+ tests)
5. `scripts/ingest.py` + scope YAML (+ tests); manual dev-index run

## V1 source map (read ONLY the files named for the step you're on; don't scan V1)
| Step | Copy from (V1) | Into (`app/`) | What it holds |
|---|---|---|---|
| 1 | `common/exceptions.py` (35 lines) | `common/exceptions.py` | `ExternalServiceError` + `AuthError`, `RateLimitError`, `ExternalTimeoutError`, `InvalidResponseError`. Drop `PlannerError`. |
| 1 | `services/http/retry_policy.py` (49) | `common/retry_policy.py` | `build_retry(is_retryable=…)` tenacity factory; reads `RETRY_*` from settings. |
| 1 | `config/logging_config.py` (86) | `config/logging_config.py` | structlog `configure_logging`, `get_logger`. Drop `plan_context_scope` and the `services.fetch.comment_pipeline` logger line. |
| 2 | `services/reddit_client/session.py` (168) | `loaders/reddit/client.py` | OAuth client-credentials token refresh, async lock. Keep `from_env` only; drop keyring/SSM/`resolve_env_or_ssm_secret`. |
| 2 | `services/reddit_client/endpoints.py` (125) | `loaders/reddit/client.py` | `search_subreddit`, `paginate_search`, `fetch_comments` (depth 1, sort top, limit 50), `_is_retryable_request` (timeout/connect, 429/5xx). Add listing endpoint `/r/{sub}/{sort}`. |
| 2 | `services/reddit_client/client.py` (108) | `loaders/reddit/client.py` | `httpx` → typed error `_translate`; async context manager. |
| 2 | `services/fetch/reddit_validation.py` (106) | `loaders/reddit/filters.py` | Post vetoes: deleted/removed, AutoModerator, ads UI, non-self, showcase (image + brag phrase + karma ≥ 150), NSFW. Showcase phrases come from `keyword_groups.NEGATIVE_KEYWORDS["showcase_brag"]` (grep that one group; inline as a tuple). |
| 2 | `services/fetch/content_filters.py` (39) | `loaders/reddit/filters.py` | `MIN_POST_LENGTH=250`, `MIN_COMMENT_LENGTH=140`, seen-id helpers. |
| 2 | `services/fetch/comment_pipeline.py` (74) | `loaders/reddit/filters.py` | `filter_comments`: dedup, AutoMod, deleted, karma ≥ 2, min length, sort by karma, cap N. |
| 2 | `services/fetch/utils/text_utils.py` (31) | `loaders/reddit/filters.py` | `clean_text` (markdown-it → bs4 → strip links/non-ASCII). |
| 3 | `services/fetch/reddit_builders.py` (101) — `post_permalink` only | `loaders/reddit/loader.py` | Canonical permalink logic. |
| 3 | `services/fetch/reddit_fetcher.py` (228) — `_fetch_posts_for_pair` only | `loaders/reddit/loader.py` | Two-phase pattern: stream/filter posts, then `asyncio.gather` comment fetches; drop posts with zero surviving comments. |
| test pattern | `tests/services/reddit_client/test_endpoints.py` | `tests/app/loaders/` | `AsyncMock(spec=httpx.AsyncClient)`, autouse fixture patching `asyncio.sleep`. |
| CLI pattern | `scripts/runs/run_fetch_preview.py` | `scripts/ingest.py` | typer style (`typer.Typer(add_completion=False)`). |

Not copied on purpose: keyword relevance scoring (`scoring.py`, `keyword_groups.py` beyond showcase), embeddings/ranking/SQLite cache, planner, keyring/SSM, `Post`/`Comment`/`FetchResult` schemas.

## Verification
- `pytest tests/app` (run only when you say so, per your preference); `mypy app scripts/ingest.py`; `ruff check app`.
- `grep -rE "^(from|import) (services|agent|common|config|api)\b" app scripts/ingest.py` → no V1 imports.
- `python scripts/ingest.py --loader reddit --dry-run` (needs REDDIT_* env), then real run against the dev index; confirm vectors + metadata in Pinecone console; re-run and confirm vector count unchanged; `echo $?` for exit codes.

## Flags
- Docs: `architecture.md` doesn't name the quality field — this plan uses `quality_score`; update the doc if you agree (untracked file, not committed).
- No CODEMAP.md exists; skipped.
- Ingestion isn't an agent/graph run, so no LangSmith tracing is added here (tracing starts in step 2).
