import pytest

from app.services.reranker import MovieReranker


def test_including_watched_removes_penalty_without_hiding_watched_status():
    reranker = MovieReranker()
    candidate = {"id": "1", "distance": 0.5}
    memory = {"watched_movie_ids": {"1"}}

    included, = reranker.rerank([candidate.copy()], memory, 1, include_watched=True)
    fallback, = reranker.rerank([candidate.copy()], memory, 1)

    assert included["watched"] is True
    assert included["ranking_signals"]["watched_penalty"] == 0
    assert fallback["ranking_signals"]["watched_penalty"] == reranker.WATCHED_PENALTY
    assert included["final_score"] - fallback["final_score"] == pytest.approx(
        reranker.WATCHED_PENALTY
    )
