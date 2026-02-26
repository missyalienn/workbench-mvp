"""SQLite-backed vector store implementation.

Summary:
    Stores embeddings in a local SQLite database using the shared cache module.

Usage:
    from services.embedding.stores.sqlite_store import SQLiteVectorStore

    store = SQLiteVectorStore("data/embedding_cache.sqlite3")
    store.set_embedding(digest, model, dims, vector)
    result = store.get_embedding(digest, model)
"""

from __future__ import annotations

from services.embedding.cache import get_embedding, init_cache, set_embedding
from services.embedding.store import VectorStore


class SQLiteVectorStore(VectorStore):
    """SQLite vector store wrapper using embedding cache helpers."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        init_cache(self._db_path)

    def get_embedding(self, content_digest: str, model: str) -> tuple[list[float], int] | None:
        return get_embedding(self._db_path, content_digest, model)

    def set_embedding(
        self,
        content_digest: str,
        model: str,
        dims: int,
        vector: list[float],
    ) -> None:
        set_embedding(self._db_path, content_digest, model, dims, vector)
