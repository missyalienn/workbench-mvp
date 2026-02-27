"""Vector store factory based on settings.

Summary:
    Returns the configured vector store implementation.

Usage:
    from services.embedding.store_factory import get_vector_store

    store = get_vector_store()
"""

from __future__ import annotations

from config.settings import settings
from services.embedding.store import VectorStore
from services.embedding.stores.sqlite_store import SQLiteVectorStore


def get_vector_store() -> VectorStore:
    """Return the configured vector store implementation."""
    store_type = settings.VECTOR_STORE_TYPE.lower().strip()
    if store_type == "sqlite":
        return SQLiteVectorStore(settings.EMBEDDING_CACHE_PATH)
    raise ValueError(f"Unsupported vector store type: {settings.VECTOR_STORE_TYPE}")
