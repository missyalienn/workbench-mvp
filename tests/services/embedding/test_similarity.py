"""Cosine similarity tests.

Usage:
    pytest tests/services/embedding/test_similarity.py
"""

import pytest

from services.embedding.similarity import cosine_similarity


def test_identical_vectors() -> None:
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_zero_vector() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_length_mismatch() -> None:
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0
