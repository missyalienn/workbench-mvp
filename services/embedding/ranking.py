"""Semantic ranking helpers.

Summary:
    Holds query-embedding and ranking inputs for semantic scoring.

Usage:
    from services.embedding.client import EmbeddingClient
    from services.embedding.ranking import RankingInput, embed_query

    ranking_input = RankingInput(query="how to bleed a radiator", candidates=[])
    query_vec, dims = embed_query(ranking_input, embedder)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from config.settings import settings
from services.embedding.client import EmbeddingClient, EmbeddingError

if TYPE_CHECKING:
    from services.fetch.reddit_fetcher import PostCandidate


@dataclass(frozen=True)
class RankingInput:
    """Inputs required for semantic ranking."""

    query: str
    candidates: list["PostCandidate"]


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    return text[:max_chars]


def embed_query(
    ranking_input: RankingInput,
    embedder: EmbeddingClient,
) -> tuple[list[float], int]:
    """Compute the query embedding once per run.

    Raises EmbeddingError if the embedding cannot be retrieved.
    """
    query = _truncate_text(ranking_input.query, settings.MAX_EMBED_TEXT_CHARS)
    if not query.strip():
        raise EmbeddingError("Query text is empty after truncation")
    return embedder.get_or_create_embedding(query)
