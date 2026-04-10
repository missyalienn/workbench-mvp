# HTTP Retry Refactor

## Root Problem

`services/http/retry_policy.py` tries to unify two unrelated things under one retry abstraction:

1. Reddit API calls (via `requests`)
2. OpenAI embedding calls (via `openai` SDK)

These have different exception types, different retry semantics, and no business sharing infrastructure. Everything downstream is a consequence of this original design flaw.

### Specific symptoms

- `RetryableFetchError` wraps three structurally different failure modes — HTTP errors (have a status code), timeouts (no response), and transport errors (no response) — into one flat class. Callers cannot distinguish them.
- `RateLimitError` is a custom class that duplicates what `requests.HTTPError` already represents when `status_code == 429`.
- `EmbeddingRetryableError(RetryableFetchError)` is a hack to plug the OpenAI client into a decorator designed for `requests`. It inherits from a class that means nothing for the embedding context.
- HTTP status codes are discarded at the raise site and unavailable to callers and log sites.
- `fetch_with_retry` accepts a `logger` parameter and passes it to tenacity's `after_log`, but `after_log` requires a stdlib logger — passing a structlog logger silently breaks retry logging.

---

## Design Principles

1. **No custom exception classes.** Use the exceptions provided by each client library — they are well-documented, well-known, and carry exactly the data that exists at each failure mode.
2. **No provider names in shared modules.** A shared retry helper should not know about Reddit, OpenAI, or any specific provider. Provider-specific knowledge lives in the provider's own module.
3. **Each client owns its retry predicate.** The client module knows what exceptions its library raises and what status codes are retryable. This logic belongs there, not in a shared utility.
4. **Separation of concerns.** Shared infrastructure provides the mechanism (retry loop, backoff, settings). Each client provides the policy (what to retry).

---

## New Architecture

### `services/http/retry_policy.py` — generic retry builder only

Provides a single `build_retry(is_retryable)` factory. Reads retry settings (max attempts, wait params) from `config/settings.py`. Has no knowledge of `requests`, `openai`, or any external provider.

```python
def build_retry(*, is_retryable: Callable[[Exception], bool]) -> Callable:
    """Return a tenacity retry decorator using the provided predicate and shared settings."""
    return retry(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_random_exponential(
            multiplier=settings.RETRY_WAIT_MULTIPLIER,
            max=settings.RETRY_WAIT_MAX,
        ),
        after=after_log(_logger, logging.WARNING),
        reraise=True,
    )
```

**Deleted from this module:** `RetryableFetchError`, `RateLimitError`, `fetch_with_retry`.

---

### `services/reddit_client/` — owns its own retry predicate

A `_is_retryable_request` predicate lives here. It understands `requests` exception types and which HTTP status codes should be retried.

```python
import requests

def _is_retryable_request(exc: Exception) -> bool:
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        return status in (429, 500, 502, 503, 504)
    return False

_reddit_retry = build_retry(is_retryable=_is_retryable_request)
```

Applied as `@_reddit_retry` in `endpoints.py`. The explicit `if response.status_code == 429` check is removed — `raise_for_status()` handles 429 as `requests.HTTPError`, and the predicate routes it correctly.

Callers (`reddit_fetcher.py`) catch `requests.exceptions.RequestException` directly. Status codes are logged from `exc.response.status_code` where available.

---

### `services/embedding/` — owns its own retry predicate

A `_is_retryable_openai` predicate lives here. It understands `openai` SDK exception types.

```python
import openai

def _is_retryable_openai(exc: Exception) -> bool:
    return isinstance(exc, (
        openai.RateLimitError,
        openai.APITimeoutError,
        openai.APIConnectionError,
        openai.InternalServerError,
    ))

_embedding_retry = build_retry(is_retryable=_is_retryable_openai)
```

Applied as `@_embedding_retry` in `services/embedding/client.py`. `EmbeddingRetryableError` is deleted. The catch block in `EmbeddingClient.embed` (formerly `get_or_create_embedding`) catches `openai.APIError` (base class for all openai SDK errors) and re-raises as `EmbeddingError`. The same decorator is applied to `_fetch_embeddings` (batch path).

---

## Migration: What Changes Where

| File | Action |
|---|---|
| `services/http/retry_policy.py` | Rewrite: remove all custom exception classes, expose only `build_retry` |
| `services/reddit_client/endpoints.py` | Add `_is_retryable_request` predicate + `_reddit_retry` decorator; remove custom raises; use `raise_for_status()` throughout |
| `services/fetch/reddit_fetcher.py` | Catch `requests.exceptions.RequestException`; log `status_code` from `exc.response` when present |
| `services/embedding/client.py` | Add `_is_retryable_openai` predicate + `_embedding_retry` decorator; remove `EmbeddingRetryableError` |
| `tests/services/reddit_client/test_endpoints.py` | Update exception assertions to `requests` types |
| `tests/services/fetch/test_reddit_fetcher.py` | Update exception types |

---

## Deleted Entirely

- `RetryableFetchError` — replaced by `requests.exceptions` types
- `RateLimitError` (custom) — replaced by `requests.HTTPError` + status predicate
- `EmbeddingRetryableError` — replaced by `openai.APIError` subtypes
- `fetch_with_retry` factory function — replaced by `build_retry`

---

## Future Extensibility

Adding a new provider (Pinecone, GitHub, Slack, etc.) requires:

1. Define `_is_retryable_<provider>` in that provider's module
2. Call `build_retry(is_retryable=_is_retryable_<provider>)`
3. Apply the resulting decorator at the call site

No changes to `retry_policy.py`. No provider names leak into shared infrastructure.

---

## HTTP Status Code Logging

After this refactor, status codes are logged at catch sites in `reddit_fetcher.py`:

```python
except requests.exceptions.RequestException as exc:
    status_code = getattr(getattr(exc, "response", None), "status_code", None)
    logger.warning("fetch.request_failed", status_code=status_code, error=str(exc))
```

For the OpenAI/embedding client, after retries are exhausted `openai.APIError` is caught in `EmbeddingClient.embed` and re-raised as `EmbeddingError`. In the batch path (`embed_texts`), chunk failures are caught and logged at the chunk level (`embedding.chunk_failed`) with `n_affected` — the caller receives `None` for affected items rather than an exception.

