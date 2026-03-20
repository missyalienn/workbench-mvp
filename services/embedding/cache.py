"""SQLite embedding cache.

Summary:
    Small, idempotent cache for embedding vectors keyed by content digest + model.

Usage:
    from services.embedding.cache import init_cache, get_embedding, set_embedding

    init_cache("data/embedding_cache.sqlite3")
    result = get_embedding("data/embedding_cache.sqlite3", digest, model)
    if result is None:
        set_embedding("data/embedding_cache.sqlite3", digest, model, dims, vector)
"""

from __future__ import annotations

import sqlite3
from array import array
from typing import Iterable

from config.logging_config import get_logger

logger = get_logger(__name__)

_TABLE_NAME = "embeddings"
_FLOAT32_ITEMSIZE = array("f").itemsize
_BUSY_TIMEOUT_MS = 5000


def _connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=_BUSY_TIMEOUT_MS / 1000)
    connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    return connection


def init_cache(db_path: str) -> None:
    """Initialize the SQLite cache schema and connection settings."""
    try:
        with _connect(db_path) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
                    content_digest TEXT NOT NULL,
                    model TEXT NOT NULL,
                    dims INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    PRIMARY KEY (content_digest, model)
                )
                """
            )
            connection.commit()
    except sqlite3.Error as exc:
        logger.warning("Embedding cache init failed: %s", exc)


def serialize_vector(vector: Iterable[float]) -> bytes:
    """Serialize a float vector into float32 bytes."""
    buffer = array("f", vector)
    return buffer.tobytes()


def deserialize_vector(blob: bytes, dims: int) -> list[float] | None:
    """Deserialize float32 bytes into a float vector.

    Returns None when the blob length does not match dims.
    """
    if dims <= 0:
        return None
    expected_size = dims * _FLOAT32_ITEMSIZE
    if len(blob) != expected_size:
        return None
    buffer = array("f")
    buffer.frombytes(blob)
    return list(buffer)


def get_embedding(
    db_path: str,
    content_digest: str,
    model: str,
) -> tuple[list[float], int] | None:
    """Fetch an embedding by (content_digest, model)."""
    try:
        with _connect(db_path) as connection:
            cursor = connection.execute(
                f"SELECT dims, embedding FROM {_TABLE_NAME} "
                "WHERE content_digest = ? AND model = ?",
                (content_digest, model),
            )
            row = cursor.fetchone()
        if not row:
            return None
        dims, blob = row
        vector = deserialize_vector(blob, int(dims))
        if vector is None:
            logger.warning(
                "Embedding cache entry invalid (digest=%s, model=%s)",
                content_digest,
                model,
            )
            return None
        return vector, int(dims)
    except sqlite3.Error as exc:
        logger.warning("Embedding cache read failed: %s", exc)
        return None


def set_embedding(
    db_path: str,
    content_digest: str,
    model: str,
    dims: int,
    vector: Iterable[float],
) -> None:
    """Store an embedding by (content_digest, model)."""
    try:
        blob = serialize_vector(vector)
        with _connect(db_path) as connection:
            connection.execute(
                f"""
                INSERT INTO {_TABLE_NAME} (content_digest, model, dims, embedding)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(content_digest, model)
                DO UPDATE SET dims = excluded.dims, embedding = excluded.embedding
                """,
                (content_digest, model, int(dims), blob),
            )
            connection.commit()
    except sqlite3.Error as exc:
        logger.warning("Embedding cache write failed: %s", exc)
