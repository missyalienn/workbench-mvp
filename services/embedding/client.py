"""OpenAI embedding client with cache support.

Summary:
    Normalizes text, computes a content digest, and returns cached or freshly
    computed embeddings using the OpenAI API.

Usage:
    from agent.clients.openai_client import get_openai_client
    from services.embedding.client import OpenAIEmbeddingClient

    client = get_openai_client()
    from services.embedding.stores.sqlite_store import SQLiteVectorStore

    store = SQLiteVectorStore("data/embedding_cache.sqlite3")
    embedder = OpenAIEmbeddingClient(
        client=client,
        model="text-embedding-3-small",
        store=store,
    )
    vector, dims = embedder.get_or_create_embedding("some text")
"""

from __future__ import annotations

import hashlib

from openai import OpenAI

from config.logging_config import get_logger
from services.fetch.utils.text_utils import clean_text
from services.http.retry_policy import RetryableFetchError, fetch_with_retry
from services.embedding.store import VectorStore

logger = get_logger(__name__)


class EmbeddingError(RuntimeError):
    """Raised when an embedding cannot be retrieved."""


class OpenAIRetryableError(RetryableFetchError):
    """Retryable transport error specific to OpenAI embedding calls."""


def normalize_text(text: str) -> str:
    """Normalize text for deterministic hashing and embedding."""
    return clean_text(text)


def content_digest(normalized_text: str) -> str:
    """Return a stable digest for normalized text."""
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


@fetch_with_retry(logger=logger)
def _fetch_embedding(*, client: OpenAI, model: str, text: str) -> list[float]:
    try:
        response = client.embeddings.create(
            model=model,
            input=text,
        )
        embedding = response.data[0].embedding
        return list(embedding)
    except Exception as exc:  # Transport failures aren't deterministic in tests.
        raise OpenAIRetryableError("Embedding request failed") from exc


class OpenAIEmbeddingClient:
    """Embedding client with cache lookup and write-back."""

    def __init__(self, *, client: OpenAI, model: str, store: VectorStore) -> None:
        self._client = client
        self._model = model
        self._store = store

    def get_or_create_embedding(self, text: str) -> tuple[list[float], int]:
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
        except RetryableFetchError as exc:
            raise EmbeddingError("Failed to fetch embedding") from exc

        dims = len(vector)
        self._store.set_embedding(digest, self._model, dims, vector)
        return vector, dims


__all__ = [
    "EmbeddingError",
    "OpenAIEmbeddingClient",
    "content_digest",
    "normalize_text",
]
