"""Embedding client tests.

Usage:
    pytest tests/services/embedding/test_client.py
"""

from types import SimpleNamespace

import pytest

from services.embedding.client import OpenAIEmbeddingClient, content_digest, normalize_text


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

    from services.embedding.cache import init_cache, set_embedding

    init_cache(db_path)
    set_embedding(db_path, digest, model, len(vector), vector)

    embedder = OpenAIEmbeddingClient(
        client=DummyClient(),
        model=model,
        cache_path=db_path,
    )

    result_vector, dims = embedder.get_or_create_embedding("abc123")
    assert dims == len(vector)
    assert result_vector == pytest.approx(vector)
