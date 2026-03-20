"""Ranking input tests.

Usage:
    pytest tests/services/embedding/test_ranking_input.py
"""

from services.embedding.ranking import RankingInput


def test_ranking_input_fields() -> None:
    candidates = []
    query = "how to bleed a radiator"
    ranking_input = RankingInput(query=query, candidates=candidates)

    assert ranking_input.query == query
    assert ranking_input.candidates == candidates
