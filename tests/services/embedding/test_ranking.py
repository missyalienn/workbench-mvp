"""Semantic ranking tests.

Usage:
    pytest tests/services/embedding/test_ranking.py
"""

from dataclasses import dataclass

import pytest

from services.embedding.client import EmbeddingError
from services.embedding.ranking import RankingInput, embed_query, rank_candidates
from services.embedding.similarity import cosine_similarity


@dataclass(frozen=True)
class DummyCandidate:
    raw_post: dict
    cleaned_title: str
    cleaned_body: str
    comments: list
    fetched_at: float


class DummyEmbedder:
    def __init__(self, vectors: dict[str, list[float]], fail_texts: set[str] | None = None) -> None:
        self._vectors = vectors
        self._fail_texts = fail_texts or set()

    def get_or_create_embedding(self, text: str):
        if text in self._fail_texts:
            raise EmbeddingError("fail")
        return self._vectors[text], len(self._vectors[text])


def _make_candidate(post_id: str, title: str, body: str):
    return DummyCandidate(
        raw_post={"id": post_id, "score": 1, "subreddit": "diy", "permalink": f"/r/diy/{post_id}"},
        cleaned_title=title,
        cleaned_body=body,
        comments=[],
        fetched_at=1.0,
    )


def test_rank_candidates_scoring() -> None:
    query = "q"
    candidates = [
        _make_candidate("1", "a", "b"),
        _make_candidate("2", "c", "d"),
    ]
    ranking_input = RankingInput(query=query, candidates=candidates)

    vectors = {
        query: [1.0, 0.0],
        "a\n\nb": [1.0, 0.0],
        "c\n\nd": [0.0, 1.0],
    }
    embedder = DummyEmbedder(vectors)

    query_embedding = embed_query(ranking_input, embedder)
    scored = rank_candidates(ranking_input, query_embedding, embedder)

    scores = [post.relevance_score for post in scored]
    assert scores[0] == pytest.approx(cosine_similarity([1.0, 0.0], [1.0, 0.0]))
    assert scores[1] == pytest.approx(cosine_similarity([1.0, 0.0], [0.0, 1.0]))


def test_rank_candidates_post_embedding_failure() -> None:
    query = "q"
    candidates = [_make_candidate("1", "a", "b")]
    ranking_input = RankingInput(query=query, candidates=candidates)

    vectors = {
        query: [1.0, 0.0],
        "a\n\nb": [1.0, 0.0],
    }
    embedder = DummyEmbedder(vectors, fail_texts={"a\n\nb"})

    query_embedding = embed_query(ranking_input, embedder)
    scored = rank_candidates(ranking_input, query_embedding, embedder)

    assert scored[0].relevance_score == 0.0


def test_embed_query_failure() -> None:
    query = "q"
    candidates = []
    ranking_input = RankingInput(query=query, candidates=candidates)

    vectors = {}
    embedder = DummyEmbedder(vectors, fail_texts={query})

    with pytest.raises(EmbeddingError):
        embed_query(ranking_input, embedder)
