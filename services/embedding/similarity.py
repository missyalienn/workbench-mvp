"""Cosine similarity helper for embedding vectors.

Summary:
    Provides a minimal cosine similarity implementation with safe guards.

Usage:
    from services.embedding.similarity import cosine_similarity

    score = cosine_similarity([1.0, 0.0], [0.5, 0.5])
"""

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Return cosine similarity between two vectors.

    Returns 0.0 for empty inputs, length mismatch, or zero-norm vectors.
    """
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=True):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
