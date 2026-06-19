from types import SimpleNamespace
from typing import Any

from app.agents.movie_agent import MovieAgent
from app.db.schemas import MovieIntent, RecommendRequest
from app.services.recommendation_formatter import RecommendationFormatter


class FakeIntentParser:
    provider = "fake"
    model = "fake-intent"

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def parse_intent(
        self,
        query: str,
        use_llm_intent: bool,
    ) -> MovieIntent:
        self.calls.append("parse_intent")

        return MovieIntent(
            raw_query=query,
            query_rewrite="rewritten emotional science fiction",
            reference_movies=["Her"],
            moods=["quiet"],
            themes=["identity"],
            genres=["Science Fiction"],
            pacing="medium",
            tone=["emotional"],
            avoid=["too slow"],
            constraints=[],
            confidence=0.9,
            parser_notes="Fake parser result.",
        )

    def get_provider_name(
        self,
        use_llm_intent: bool,
    ) -> str:
        return "fake-intent"


class FakeMemoryService:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def get_reranking_memory(
        self,
        db: Any,
        user_id: str,
    ) -> dict[str, Any]:
        self.calls.append("load_memory")

        return {
            "liked_genres": {"Science Fiction": 1},
            "disliked_genres": {},
            "watched_movie_ids": set(),
            "saved_movie_ids": set(),
            "liked_movie_ids": set(),
            "disliked_movie_ids": set(),
        }


class FakeVectorStore:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.collection_name = "fake-collection"

        self.embedding_service = SimpleNamespace(
            provider="fake",
            model_name="fake-embedding",
        )

    def count(self) -> int:
        return 2

    def search(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        self.calls.append("retrieve")

        assert query == (
            "rewritten emotional science fiction"
        )

        return [
            {
                "id": "1",
                "title": "Movie One",
                "release_year": 2020,
                "genres": "Science Fiction, Drama",
                "distance": 0.2,
                "document": "Movie One document.",
                "popularity": 10.0,
                "vote_average": 7.5,
                "vote_count": 500,
            },
            {
                "id": "2",
                "title": "Movie Two",
                "release_year": 2021,
                "genres": "Drama",
                "distance": 0.3,
                "document": "Movie Two document.",
                "popularity": 8.0,
                "vote_average": 7.0,
                "vote_count": 300,
            },
        ]


class FakeReranker:
    SEMANTIC_WEIGHT = 0.70
    PREFERENCE_WEIGHT = 0.15
    NOVELTY_WEIGHT = 0.10
    DIVERSITY_WEIGHT = 0.12

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def filter_watched_candidates(
        self,
        candidates: list[dict[str, Any]],
        user_memory: dict[str, Any],
        include_watched: bool,
    ) -> tuple[list[dict[str, Any]], int]:
        self.calls.append("filter_watched")

        return candidates, 0

    def rerank(
        self,
        candidates: list[dict[str, Any]],
        user_memory: dict[str, Any],
        top_k: int,
    ) -> list[dict[str, Any]]:
        self.calls.append("rerank")

        result: list[dict[str, Any]] = []

        for index, candidate in enumerate(
            candidates[:top_k]
        ):
            candidate = candidate.copy()

            candidate.update(
                {
                    "semantic_score": 0.8 - index * 0.1,
                    "preference_score": 0.2,
                    "novelty_score": 0.4,
                    "diversity_penalty": 0.0,
                    "final_score": 0.7 - index * 0.1,
                    "preference": None,
                    "watched": False,
                    "saved": False,
                    "ranking_signals": {
                        "semantic_score": 0.8,
                        "final_score": 0.7,
                    },
                }
            )

            result.append(candidate)

        return result


class FakeExplanationService:
    provider = "fake"
    model = "fake-explanation"

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def generate_explanations(
        self,
        query: str,
        recommendations: list[dict[str, Any]],
        use_llm_explanation: bool,
    ) -> list[str]:
        self.calls.append("explain")

        return [
            f"Explanation for {item['title']}."
            for item in recommendations
        ]

    def get_provider_name(
        self,
        use_llm_explanation: bool,
    ) -> str:
        return "fake-explanation"


def test_movie_agent_coordinates_tools_in_order() -> None:
    calls: list[str] = []

    agent = MovieAgent(
        intent_parser=FakeIntentParser(calls),
        memory_service=FakeMemoryService(calls),
        vector_store=FakeVectorStore(calls),
        reranker=FakeReranker(calls),
        explanation_service=(
            FakeExplanationService(calls)
        ),
        formatter=RecommendationFormatter(),
    )

    request = RecommendRequest(
        user_id="test_user",
        query="something like Her",
        top_k=2,
        include_watched=False,
        use_llm_explanations=False,
        use_llm_intent=True,
        include_agent_trace=True,
    )

    response = agent.recommend(
        db=None,  # Fake memory service ignores the DB.
        request=request,
    )

    assert calls == [
        "parse_intent",
        "load_memory",
        "retrieve",
        "filter_watched",
        "rerank",
        "explain",
    ]

    assert response.retrieval_query == (
        "rewritten emotional science fiction"
    )

    assert len(response.results) == 2
    assert response.results[0].title == "Movie One"

    assert response.agent_trace is not None

    trace_names = [
        step.name
        for step in response.agent_trace.steps
    ]

    assert trace_names == [
        "validate_tools",
        "parse_intent",
        "load_user_memory",
        "retrieve_candidates",
        "filter_watched_candidates",
        "heuristic_rerank",
        "bounded_llm_rerank",
        "generate_explanations",
        "format_response",
    ]

    bounded_step = next(
        step
        for step in response.agent_trace.steps
        if step.name == "bounded_llm_rerank"
    )

    assert bounded_step.status == "skipped"