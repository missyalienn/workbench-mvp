# 0005 — Containerized FastAPI, off Lambda

**Status:** Accepted (2026-10-19) — host TBD

**Context:** V1 runs on Lambda via Mangum behind API Gateway (29s timeout, poor streaming). Multi-tool agent turns with streaming don't fit.

**Decision:**
- V2 is a new FastAPI app in `app/`, packaged as one Docker container; local Docker first.
- Host-agnostic: config from env, no cloud-provider code in the app.
- Hosting choice deferred (FastAPI Cloud is a candidate); minimize cloud spend.
- V1 stays on Lambda, untouched, until cutover; then deleted.

**Consequences:**
- Ingestion CLI is pure args + exit codes so it converts to a scheduled job once hosted.
