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

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from config.logging_config import get_logger
from config.settings import settings
from services.embedding.client import EmbeddingClient, EmbeddingError
from services.embedding.similarity import cosine_similarity
from services.fetch.reddit_builders import build_post_model
from services.fetch.schemas import Post

if TYPE_CHECKING:
    from services.fetch.reddit_fetcher import PostCandidate

logger = get_logger(__name__)


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


def rank_candidates(
    ranking_input: RankingInput,
    query_embedding: tuple[list[float], int],
    embedder: EmbeddingClient,
) -> list[Post]:
    """Return scored Post models from candidates."""
    t0 = time.monotonic()
    logger.info("ranking.start", n_candidates=len(ranking_input.candidates))
    query_vector, _ = query_embedding
    scored: list[Post] = []
    for candidate in ranking_input.candidates:
        post_text = _truncate_text(
            f"{candidate.cleaned_title}\n\n{candidate.cleaned_body}",
            settings.MAX_EMBED_TEXT_CHARS,
        )
        try:
            post_vector, _ = embedder.get_or_create_embedding(post_text)
            score = cosine_similarity(query_vector, post_vector)
        except EmbeddingError as exc:
            logger.warning("ranking.embedding_failed", post_id=candidate.raw_post.get("id"), error=str(exc))
            score = 0.0

        scored.append(
            build_post_model(
                # URL, karma, and subreddit are derived from raw_post in build_post_model.
                raw_post=candidate.raw_post,
                cleaned_title=candidate.cleaned_title,
                cleaned_body=candidate.cleaned_body,
                relevance_score=score,
                matched_keywords=[],
                comments=candidate.comments,
                fetched_at=candidate.fetched_at,
            )
        )
    logger.info("ranking.complete", elapsed_ms=int((time.monotonic() - t0) * 1000), n_ranked=len(scored))
    return scored


def zero_score_posts(candidates: list["PostCandidate"]) -> list[Post]:
    scored: list[Post] = []
    for candidate in candidates:
        scored.append(
            build_post_model(
                # URL, karma, and subreddit are derived from raw_post in build_post_model.
                raw_post=candidate.raw_post,
                cleaned_title=candidate.cleaned_title,
                cleaned_body=candidate.cleaned_body,
                relevance_score=0.0,
                matched_keywords=[],
                comments=candidate.comments,
                fetched_at=candidate.fetched_at,
            )
        )
    return scored
