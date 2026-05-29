import time
from typing import Any

from app.db.schemas import MovieRecommendation, RecommendResponse
from app.services.vector_store import MovieVectorStore


class RecommenderService:
    """
    Main recommendation service.

    For Day 4, this service uses semantic vector search only.
    Later, this is where we will add:
    - metadata filtering
    - user preference memory
    - reranking
    - diversity control
    - LLM-based explanations
    """

    def __init__(self) -> None:
        self.vector_store = MovieVectorStore()
    

    def recommend(self, user_id: str, query: str, top_k: int = 5) -> RecommendResponse:
        """
        Return movie recommendations for a natural-language query.
        """
        start_time = time.perf_counter() # Start timer for latency measurement

        if self.vector_store.count() == 0:
            raise ValueError("Vector store is empty. Please build the vector database first.")
        
        raw_results = self.vector_store.search(query=query, top_k=top_k)

        recommendations = [
            self._format_recommendation(result) for result in raw_results
        ]

        latency_ms = (time.perf_counter() - start_time) * 1000 # Convert to milliseconds

        return RecommendResponse(
            user_id=user_id,
            query=query,
            top_k=top_k,
            results=recommendations,
            latency_ms=round(latency_ms, 2),
        )


    def _format_recommendation(self, result: dict[str, Any]) -> MovieRecommendation:
        """
        Convert raw vector search result into API response format.
        """
        distance = float(result.get("distance", 0.0))
        score = self._distance_to_score(distance)

        document = result.get("document", "") or ""
        document_preview = self._make_document_preview(document)

        title = result.get("title") or "Unknown Title"
        release_year = result.get("release_year")
        if release_year == -1:
            release_year = None
        
        reason = self._generate_simple_reason(
            title=title,
            genres=result.get("genres"),
            score=score,
        )

        return MovieRecommendation(
            movie_id=str(result.get("id")),
            title=title,
            release_year=release_year,
            genres=result.get("genres"),
            score=score,
            distance=round(distance, 4),
            reason=reason,
            document_preview=document_preview,
        )


    def _distance_to_score(self, distance: float) -> float:
        """
        Convert vector distance into a more intuitive score.

        Chroma returns a distance where smaller usually means more similar.
        We convert it into a score where larger means better.

        This is not a calibrated probability. It is just a user-friendly
        retrieval score for display and debugging.
        """
        score = 1.0 / (1.0 + max(distance, 0.0))
        return round(score, 4)
    

    def _make_document_preview(self, document: str, max_chars: int = 500) -> str:
        """
        Shorten the full movie document for API response display.
        """
        document = document.strip()

        if len(document) <= max_chars:
            return document

        return document[:max_chars].rstrip() + "..."
    

    def _generate_simple_reason(
        self,
        title: str,
        genres: str | None,
        score: float,
    ) -> str:
        """
        Temporary non-LLM explanation.

        Later we will replace or improve this with LLM-grounded explanations.
        For now, we avoid hallucination by only using available metadata.
        """
        if genres:
            return (
                f"Recommended because {title} is semantically close to your query "
                f"and belongs to genres such as {genres}. Retrieval score: {score:.2f}."
            )

        return (
            f"Recommended because {title} is semantically close to your query. "
            f"Retrieval score: {score:.2f}."
        )