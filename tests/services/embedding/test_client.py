"""Embedding client tests.

Usage:
    pytest tests/services/embedding/test_client.py
"""

from types import SimpleNamespace

import pytest

from services.embedding.client import OpenAIEmbeddingClient, content_digest, normalize_text
from services.embedding.stores.sqlite_store import SQLiteVectorStore


def test_get_or_create_embedding_reads_from_cache(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    digest = content_digest(normalize_text("abc123"))
    model = "text-embedding-3-small"
    vector = [0.1, -0.2, 0.3]

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, *, model: str, input: str):
            raise AssertionError("Embedding API should not be called when cache hits")

    store = SQLiteVectorStore(db_path)
    store.set_embedding(digest, model, len(vector), vector)

    embedder = OpenAIEmbeddingClient(
        client=DummyClient(),
        model=model,
        store=store,
    )

    result_vector, dims = embedder.get_or_create_embedding("abc123")
    assert dims == len(vector)
    assert result_vector == pytest.approx(vector)
