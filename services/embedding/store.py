"""Vector store interface for embedding persistence.

Summary:
    Defines the minimal interface required by embedding and scoring components.

Usage:
    from services.embedding.store import VectorStore

    def load(store: VectorStore, digest: str, model: str):
        return store.get_embedding(digest, model)
"""

from __future__ import annotations

from typing import Protocol


class VectorStore(Protocol):
    """Minimal vector store interface for embeddings."""

    def get_embedding(self, content_digest: str, model: str) -> tuple[list[float], int] | None:
        """Return (vector, dims) or None when missing."""

    def set_embedding(
        self,
        content_digest: str,
        model: str,
        dims: int,
        vector: list[float],
    ) -> None:
        """Persist the vector under (content_digest, model)."""
