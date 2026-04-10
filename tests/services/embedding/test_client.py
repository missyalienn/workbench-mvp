"""Embedding client tests.

Usage:
    pytest tests/services/embedding/test_client.py
"""

from types import SimpleNamespace

import pytest

from services.embedding.client import EmbeddingClient, content_digest, normalize_text
from services.embedding.stores.sqlite_store import SQLiteVectorStore


def _make_api_response(vectors: list[list[float]]):
    """Build a minimal fake OpenAI embeddings response."""
    items = [
        SimpleNamespace(index=i, embedding=v)
        for i, v in enumerate(vectors)
    ]
    return SimpleNamespace(data=items)


def test_embed_reads_from_cache(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    digest = content_digest(normalize_text("abc123"))
    model = "text-embedding-3-small"
    vector = [0.1, -0.2, 0.3]

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, *, model: str, input):
            raise AssertionError("Embedding API should not be called when cache hits")

    store = SQLiteVectorStore(db_path)
    store.set_embedding(digest, model, len(vector), vector)

    embedder = EmbeddingClient(client=DummyClient(), model=model, store=store)

    result_vector, dims = embedder.embed("abc123")
    assert dims == len(vector)
    assert result_vector == pytest.approx(vector)


def test_embed_texts_all_cache_hits(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    model = "text-embedding-3-small"
    texts = ["hello", "world"]
    vectors = [[0.1, 0.2], [0.3, 0.4]]

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, *, model: str, input):
            raise AssertionError("Embedding API should not be called when all cache hits")

    store = SQLiteVectorStore(db_path)
    for text, vector in zip(texts, vectors):
        digest = content_digest(normalize_text(text))
        store.set_embedding(digest, model, len(vector), vector)

    embedder = EmbeddingClient(client=DummyClient(), model=model, store=store)
    results = embedder.embed_texts(texts)

    assert len(results) == 2
    assert results[0] == pytest.approx(vectors[0])
    assert results[1] == pytest.approx(vectors[1])


def test_embed_texts_all_cache_misses(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    model = "text-embedding-3-small"
    texts = ["hello", "world"]
    vectors = [[0.1, 0.2], [0.3, 0.4]]
    api_calls = []

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, *, model: str, input):
            api_calls.append(input)
            return _make_api_response(vectors)

    store = SQLiteVectorStore(db_path)
    embedder = EmbeddingClient(client=DummyClient(), model=model, store=store)
    results = embedder.embed_texts(texts)

    assert len(api_calls) == 1
    assert results[0] == pytest.approx(vectors[0])
    assert results[1] == pytest.approx(vectors[1])


def test_embed_texts_mixed_cache(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    model = "text-embedding-3-small"
    cached_text = "hello"
    cached_vector = [0.1, 0.2]
    miss_text = "world"
    miss_vector = [0.3, 0.4]
    api_calls = []

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, *, model: str, input):
            api_calls.append(input)
            return _make_api_response([miss_vector])

    store = SQLiteVectorStore(db_path)
    digest = content_digest(normalize_text(cached_text))
    store.set_embedding(digest, model, len(cached_vector), cached_vector)

    embedder = EmbeddingClient(client=DummyClient(), model=model, store=store)
    results = embedder.embed_texts([cached_text, miss_text])

    assert len(api_calls) == 1
    assert api_calls[0] == [normalize_text(miss_text)]
    assert results[0] == pytest.approx(cached_vector)
    assert results[1] == pytest.approx(miss_vector)


def test_embed_texts_empty_input_returns_none(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    model = "text-embedding-3-small"
    good_vector = [0.1, 0.2]
    api_calls = []

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, *, model: str, input):
            api_calls.append(input)
            return _make_api_response([good_vector])

    store = SQLiteVectorStore(db_path)
    embedder = EmbeddingClient(client=DummyClient(), model=model, store=store)
    results = embedder.embed_texts(["", "good text"])

    assert results[0] is None
    assert results[1] == pytest.approx(good_vector)


def test_embed_texts_chunk_failure_isolates(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    model = "text-embedding-3-small"
    import openai

    class DummyClient:
        def __init__(self) -> None:
            self.embeddings = SimpleNamespace(create=self._create)
            self._call_count = 0

        def _create(self, *, model: str, input):
            self._call_count += 1
            raise openai.APIConnectionError(request=None)

    store = SQLiteVectorStore(db_path)
    dummy_openai = DummyClient()
    embedder = EmbeddingClient(client=dummy_openai, model=model, store=store)

    results = embedder.embed_texts(["text one", "text two"])

    assert results[0] is None
    assert results[1] is None
