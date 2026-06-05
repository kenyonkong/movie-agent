import time
from turtle import title
from typing import Any

from sqlalchemy.orm import Session

from app.db.schemas import MovieRecommendation, RecommendResponse
from app.services.vector_store import MovieVectorStore
from app.services.reranker import MovieReranker
from app.services.memory_service import MemoryService



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

    Day 8 version:
    - Retrieves a larger candidate pool from vector search
    - Loads user preference memory from SQLite
    - Reranks candidates using semantic score + memory signals

    Day 9 version:
    - Added optionally filters watched movies
    """

    CANDIDATE_MULTIPLIER = 8 # Retrieve this many candidates from vector search before reranking
    MIN_CANDIDATE_POOL = 40 # Always retrieve at least this many candidates for reranking

    def __init__(self) -> None:
        self.vector_store = MovieVectorStore()
        self.reranker = MovieReranker()
        self.memory_service = MemoryService()
    

    def recommend(
            self,
            db: Session, 
            user_id: str, 
            query: str, 
            top_k: int = 5, 
            include_watched: bool = False) -> RecommendResponse:
        """
        Return movie recommendations for a natural-language query.
        """
        start_time = time.perf_counter() # Start timer for latency measurement

        if self.vector_store.count() == 0:
            raise ValueError("Vector store is empty. Please build the vector database first.")
        
        candidate_k = max(top_k * self.CANDIDATE_MULTIPLIER, self.MIN_CANDIDATE_POOL)

        raw_candidates = self.vector_store.search(query, top_k=candidate_k)

        user_memory = self.memory_service.get_reranking_memory(db=db, user_id=user_id)

        filtered_candidates, filtered_watched_count = self.reranker.filter_watched_candidates(
            candidates=raw_candidates,
            user_memory=user_memory,
            include_watched=include_watched,
        )

        # Fallback:
        # If filtering watched movies removes too many results, use the original
        # candidate pool so the API can still return something useful.
        candidates_for_reranking = (
            filtered_candidates
            if len(filtered_candidates) >= top_k
            else raw_candidates
        )

        reranked_results = self.reranker.rerank(
            candidates=candidates_for_reranking,
            user_memory=user_memory,
            top_k=top_k,
        )

        recommendations = [
            self._format_recommendation(result)
            for result in reranked_results
        ]

        latency_ms = (time.perf_counter() - start_time) * 1000 # Convert to milliseconds

        return RecommendResponse(
            user_id=user_id,
            query=query,
            top_k=top_k,

            include_watched=include_watched,
            candidate_count=len(raw_candidates),
            filtered_watched_count=filtered_watched_count,

            results=recommendations,
            latency_ms=round(latency_ms, 2),
        )


    def _format_recommendation(self, result: dict[str, Any]) -> MovieRecommendation:
        """
        Convert raw vector search result into API response format.
        """
        distance = float(result.get("distance", 0.0))
        final_score = float(result.get("final_score", 0.0))
        semantic_score = float(result.get("semantic_score", 0.0))
        preference_score = float(result.get("preference_score", 0.0))

        document = result.get("document", "") or ""
        document_preview = self._make_document_preview(document)

        title = result.get("title") or "Unknown Title"
        release_year = result.get("release_year")

        if release_year == -1:
            release_year = None

        watched = bool(result.get("watched", False))
        saved = bool(result.get("saved", False))
        preference = result.get("preference")
        if preference not in ("like", "dislike"):
            preference = None

        reason = self._generate_reranked_reason(
            title=title,
            genres=result.get("genres"),
            semantic_score=semantic_score,
            preference_score=preference_score,
            watched=watched,
            saved=saved,
        )

        return MovieRecommendation(
            movie_id=str(result.get("id")),
            title=title,
            release_year=release_year,
            genres=result.get("genres"),
            score=round(final_score, 4),
            distance=round(distance, 4),
            semantic_score=round(semantic_score, 4),
            preference_score=round(preference_score, 4),
            preference=preference,
            watched=watched,
            saved=saved,
            reason=reason,
            document_preview=document_preview,
            ranking_signals=result.get("ranking_signals", {}),
        )
       
    

    def _make_document_preview(self, document: str, max_chars: int = 500) -> str:
        """
        Shorten the full movie document for API response display.
        """
        document = document.strip()

        if len(document) <= max_chars:
            return document

        return document[:max_chars].rstrip() + "..."
    

    def _generate_reranked_reason(
        self, 
        title: str, 
        genres: str | None,
        semantic_score: float,
        preference_score: float,
        watched: bool,
        saved: bool,
    ) -> str:
        """
        Generate a transparent non-LLM explanation for the reranked result.
        """
        parts: list[str] = [
            f"{title} was retrieved because it semantically matches your query "
            f"(semantic score: {semantic_score:.2f})."
]

        if genres:
            parts.append(f"It belongs to genres such as {genres}.")

        if preference_score > 0:
            parts.append(
                f"It received a preference boost based on your liked genres "
                f"(preference score: {preference_score:.2f})."
            )
        elif preference_score < 0:
            parts.append(
                f"It was penalized because it overlaps with genres you disliked "
                f"(preference score: {preference_score:.2f})."
            )

        if watched:
            parts.append(
                "It was also penalized because you already marked it as watched."
            )

        if saved:
            parts.append(
                "It received a small boost because you previously saved it."
            )

        return " ".join(parts)