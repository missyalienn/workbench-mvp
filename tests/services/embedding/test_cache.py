"""Embedding cache tests.

Usage:
    pytest tests/services/embedding/test_cache.py
"""

import pytest

from services.embedding.cache import get_embedding, init_cache, set_embedding


def test_cache_round_trip(tmp_path) -> None:
    db_path = str(tmp_path / "embedding_cache.sqlite3")
    init_cache(db_path)

    digest = "digest-1"
    model = "text-embedding-3-small"
    vector = [0.1, -0.2, 0.3]

    set_embedding(db_path, digest, model, len(vector), vector)
    result = get_embedding(db_path, digest, model)

    assert result is not None
    loaded_vector, dims = result
    assert dims == len(vector)
    # Stored as float32, so allow minor rounding differences on round-trip.
    assert loaded_vector == pytest.approx(vector)


#Issue: First run failed because the test compared floats for exact equality. 
# The cache stores vectors as float32, so values round slightly (e.g., 0.1 becomes 0.10000000149). 
# Exact equality fails.
# Fix: use approximate comparison in the test (pytest.approx) so float32 round‑trip differences are accepted.
