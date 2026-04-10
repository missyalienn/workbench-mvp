"""OpenAI embedding client with cache support.

Summary:
    Normalizes text, computes a content digest, and returns cached or freshly
    computed embeddings using the OpenAI API.

Usage:
    from agent.clients.openai_client import get_openai_client
    from services.embedding.client import EmbeddingClient

    client = get_openai_client()
    from services.embedding.stores.sqlite_store import SQLiteVectorStore

    store = SQLiteVectorStore("data/embedding_cache.sqlite3")
    embedder = EmbeddingClient(
        client=client,
        model="text-embedding-3-small",
        store=store,
    )
    vector, dims = embedder.embed("some text")
    vectors = embedder.embed_texts(["text one", "text two"])
"""

from __future__ import annotations

import hashlib

import openai
from openai import OpenAI

from config.logging_config import get_logger
from services.embedding.store import VectorStore
from services.fetch.utils.text_utils import clean_text
from services.http.retry_policy import build_retry

logger = get_logger(__name__)


class EmbeddingError(RuntimeError):
    """Raised when an embedding cannot be retrieved."""


def _is_retryable_openai(exc: Exception) -> bool:
    """Return True for transient OpenAI API failures that warrant a retry."""
    return isinstance(exc, (
        openai.RateLimitError,
        openai.APITimeoutError,
        openai.APIConnectionError,
        openai.InternalServerError,
    ))


_embedding_retry = build_retry(is_retryable=_is_retryable_openai)


def normalize_text(text: str) -> str:
    """Normalize text for deterministic hashing and embedding."""
    return clean_text(text)


def content_digest(normalized_text: str) -> str:
    """Return a stable digest for normalized text."""
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


@_embedding_retry
def _fetch_embedding(*, client: OpenAI, model: str, text: str) -> list[float]:
    response = client.embeddings.create(model=model, input=text)
    return list(response.data[0].embedding)


@_embedding_retry
def _fetch_embeddings(*, client: OpenAI, model: str, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=texts)
    return [list(item.embedding) for item in sorted(response.data, key=lambda x: x.index)]


class EmbeddingClient:
    """Embedding client with cache lookup and write-back."""

    def __init__(self, *, client: OpenAI, model: str, store: VectorStore) -> None:
        self._client = client
        self._model = model
        self._store = store

    def embed(self, text: str) -> tuple[list[float], int]:
        normalized = normalize_text(text)
        if not normalized:
            raise EmbeddingError("Embedding text is empty after normalization")

        digest = content_digest(normalized)
        cached = self._store.get_embedding(digest, self._model)
        if cached is not None:
            return cached

        try:
            vector = _fetch_embedding(
                client=self._client,
                model=self._model,
                text=normalized,
            )
        except openai.APIError as exc:
            raise EmbeddingError("Failed to fetch embedding") from exc

        dims = len(vector)
        self._store.set_embedding(digest, self._model, dims, vector)
        return vector, dims

    def embed_texts(self, texts: list[str]) -> list[list[float] | None]:
        """Embed a list of texts, returning a vector per input or None on failure.

        Results are parallel to the input list. None is returned for any input
        that is empty after normalization or whose chunk fails after retries.
        Cache is checked before any API call; misses are sent in batched chunks.
        """
        _MAX_INPUTS_PER_CHUNK = 2048
        _MAX_TOKENS_PER_CHUNK = 300_000
        _CHARS_PER_TOKEN = 4

        normalized = [normalize_text(t) for t in texts]
        results: list[list[float] | None] = [None] * len(texts)

        valid_indices: list[int] = []
        for i, norm in enumerate(normalized):
            if not norm:
                logger.warning("embedding.batch_input_invalid", index=i)
                continue
            valid_indices.append(i)

        miss_indices: list[int] = []
        for i in valid_indices:
            digest = content_digest(normalized[i])
            cached = self._store.get_embedding(digest, self._model)
            if cached is not None:
                results[i] = cached[0]
            else:
                miss_indices.append(i)

        if not miss_indices:
            return results

        # Build chunks within API limits.
        chunks: list[list[int]] = []
        current_chunk: list[int] = []
        current_tokens = 0
        for i in miss_indices:
            estimated_tokens = len(normalized[i]) // _CHARS_PER_TOKEN
            if current_chunk and (
                len(current_chunk) >= _MAX_INPUTS_PER_CHUNK
                or current_tokens + estimated_tokens > _MAX_TOKENS_PER_CHUNK
            ):
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            current_chunk.append(i)
            current_tokens += estimated_tokens
        if current_chunk:
            chunks.append(current_chunk)

        for chunk_index, chunk in enumerate(chunks):
            chunk_texts = [normalized[i] for i in chunk]
            try:
                vectors = _fetch_embeddings(
                    client=self._client,
                    model=self._model,
                    texts=chunk_texts,
                )
            except openai.APIError as exc:
                logger.warning(
                    "embedding.chunk_failed",
                    chunk_index=chunk_index,
                    n_affected=len(chunk),
                    error=str(exc),
                )
                continue

            for response_index, original_index in enumerate(chunk):
                vector = vectors[response_index]
                digest = content_digest(normalized[original_index])
                self._store.set_embedding(digest, self._model, len(vector), vector)
                results[original_index] = vector

        return results


__all__ = [
    "EmbeddingError",
    "EmbeddingClient",
    "content_digest",
    "normalize_text",
    "embed_texts",
]
