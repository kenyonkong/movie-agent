from typing import Any

from app.db.schemas import MovieIntent
from app.services.bounded_llm_reranker import (
    BoundedLLMReranker,
    LLMRerankOutput,
    LLMRerankSelection,
)


def make_candidate(
    movie_id: str,
    title: str,
    score: float,
) -> dict[str, Any]:
    return {
        "id": movie_id,
        "title": title,
        "release_year": 2020,
        "genres": "Drama, Science Fiction",
        "keywords": "memory, identity",
        "director": "Test Director",
        "cast": "Actor One, Actor Two",
        "overview": f"Overview for {title}.",
        "runtime": 110,
        "original_language": "en",
        "vote_average": 7.5,
        "vote_count": 1000,
        "popularity": 20.0,
        "distance": 0.2,
        "semantic_score": 0.8,
        "preference_score": 0.1,
        "novelty_score": 0.4,
        "diversity_penalty": 0.0,
        "final_score": score,
        "watched": False,
        "saved": False,
        "preference": None,
        "ranking_signals": {
            "final_score": score,
        },
        "document": f"Title: {title}",
    }


def make_intent() -> MovieIntent:
    return MovieIntent(
        raw_query="quiet emotional sci-fi",
        query_rewrite=(
            "quiet emotional science fiction "
            "about identity"
        ),
        reference_movies=[],
        moods=["quiet", "emotional"],
        themes=["identity"],
        genres=["Science Fiction"],
        pacing="medium",
        tone=["reflective"],
        avoid=[],
        constraints=[],
        confidence=0.9,
        parser_notes="Test intent.",
    )


class ValidStubReranker(
    BoundedLLMReranker
):
    def _call_model(
        self,
        payload: dict[str, Any],
    ) -> tuple[
        LLMRerankOutput,
        dict[str, int],
    ]:
        return (
            LLMRerankOutput(
                selections=[
                    LLMRerankSelection(
                        movie_id="3",
                        reason=(
                            "Best match for the requested "
                            "reflective tone."
                        ),
                    ),
                    LLMRerankSelection(
                        movie_id="1",
                        reason=(
                            "Strong thematic and semantic fit."
                        ),
                    ),
                ],
                summary=(
                    "Prioritized tone and identity themes."
                ),
            ),
            {
                "input_tokens": 500,
                "output_tokens": 80,
            },
        )


class InvalidIdStubReranker(
    BoundedLLMReranker
):
    def _call_model(
        self,
        payload: dict[str, Any],
    ) -> tuple[
        LLMRerankOutput,
        dict[str, int],
    ]:
        return (
            LLMRerankOutput(
                selections=[
                    LLMRerankSelection(
                        movie_id="999",
                        reason="Invented candidate.",
                    ),
                    LLMRerankSelection(
                        movie_id="1",
                        reason="Valid candidate.",
                    ),
                ],
                summary="Invalid test output.",
            ),
            {
                "input_tokens": 500,
                "output_tokens": 50,
            },
        )


def test_valid_llm_reranking_reorders_candidates() -> None:
    reranker = ValidStubReranker(
        provider="openai",
        model="fake-model",
        shortlist_size=3,
    )

    candidates = [
        make_candidate("1", "Movie One", 0.9),
        make_candidate("2", "Movie Two", 0.8),
        make_candidate("3", "Movie Three", 0.7),
    ]

    result = reranker.rerank(
        original_query="quiet emotional sci-fi",
        retrieval_query=(
            "quiet emotional science fiction"
        ),
        parsed_intent=make_intent(),
        user_memory={
            "liked_genres": {},
            "disliked_genres": {},
        },
        candidates=candidates,
        top_k=2,
        enabled=True,
    )

    assert result.used_llm is True
    assert result.fallback_used is False
    assert result.selected_movie_ids == [
        "3",
        "1",
    ]

    assert result.candidates[0]["title"] == (
        "Movie Three"
    )

    assert result.candidates[0][
        "heuristic_rank"
    ] == 3

    assert result.candidates[0][
        "llm_rank"
    ] == 1

    # The heuristic numeric score remains unchanged.
    assert result.candidates[0][
        "final_score"
    ] == 0.7


def test_invalid_movie_id_falls_back_to_heuristic_order() -> None:
    reranker = InvalidIdStubReranker(
        provider="openai",
        model="fake-model",
        shortlist_size=3,
    )

    candidates = [
        make_candidate("1", "Movie One", 0.9),
        make_candidate("2", "Movie Two", 0.8),
        make_candidate("3", "Movie Three", 0.7),
    ]

    result = reranker.rerank(
        original_query="quiet emotional sci-fi",
        retrieval_query=(
            "quiet emotional science fiction"
        ),
        parsed_intent=make_intent(),
        user_memory={
            "liked_genres": {},
            "disliked_genres": {},
        },
        candidates=candidates,
        top_k=2,
        enabled=True,
    )

    assert result.used_llm is False
    assert result.fallback_used is True

    assert result.selected_movie_ids == [
        "1",
        "2",
    ]

    assert result.provider_name == (
        "heuristic:fallback"
    )

    assert result.fallback_reason is not None
    assert "outside the candidate allowlist" in (
        result.fallback_reason
    )