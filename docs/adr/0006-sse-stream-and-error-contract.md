# 0006 — SSE stream contract and errors

**Status:** Accepted (2026-10-19)

**Context:** Frontend uses Vercel AI SDK `useChat`. Errors can occur before or after the stream starts (HTTP status already sent).

**Decision:**
- Turns stream over SSE in the AI SDK stream protocol; citations sent as data parts.
- Pre-stream failures (validation, rate limit, auth): RFC 9457 problem+json, ported from V1.
- Mid-stream failures: typed error part (sanitized message + code), then close stream. Never tracebacks.
- Full error logged and traced, keyed by `thread_id`.
- Abuse/cost controls: proxy shared secret, per-IP rate limit, per-turn model/tool/`fetch_live` caps. All limits in settings.

**Consequences:**
- Citations are source-agnostic data; frontend never parses answer text for sources.
