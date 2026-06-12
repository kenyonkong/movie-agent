import time
from turtle import title
from typing import Any

from sqlalchemy.orm import Session

from app.db.schemas import MovieRecommendation, RecommendResponse
from app.services.vector_store import MovieVectorStore
from app.services.reranker import MovieReranker
from app.services.memory_service import MemoryService
from app.services.explanation_service import ExplanationService
from app.services.intent_parser import IntentParserService



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

    Day 11 version:
    - Generates grounded explanations with template or OpenAI provider
    """

    CANDIDATE_MULTIPLIER = 10 # Retrieve this many candidates from vector search before reranking
    MIN_CANDIDATE_POOL = 50 # Always retrieve at least this many candidates for reranking

    def __init__(self) -> None:
        self.vector_store = MovieVectorStore()
        self.reranker = MovieReranker()
        self.memory_service = MemoryService()
        self.explanation_service = ExplanationService()
        self.intent_parser = IntentParserService()

    def recommend(
            self,
            db: Session, 
            user_id: str, 
            query: str, 
            top_k: int = 5, 
            include_watched: bool = False, 
            use_llm_explanation: bool = False,
            use_llm_intent: bool = False,
            ) -> RecommendResponse:
        """
        Return movie recommendations for a natural-language query.
        """
        start_time = time.perf_counter() # Start timer for latency measurement

        if self.vector_store.count() == 0:
            raise ValueError("Vector store is empty. Please build the vector database first.")
        
        candidate_k = max(top_k * self.CANDIDATE_MULTIPLIER, self.MIN_CANDIDATE_POOL)

        parsed_intent = self.intent_parser.parse_intent(
            query=query, 
            use_llm_intent=use_llm_intent,
        )
        retrieval_query = parsed_intent.query_rewrite.strip() or query

        raw_candidates = self.vector_store.search(
            retrieval_query, 
            top_k=candidate_k
        )

        user_memory = self.memory_service.get_reranking_memory(
            db=db,
            user_id=user_id
        )

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

        print("=== Before rerank ===")
        for c in candidates_for_reranking[:20]:
            print(c["title"], c["genres"], c["distance"])


        reranked_results = self.reranker.rerank(
            candidates=candidates_for_reranking,
            user_memory=user_memory,
            top_k=top_k,
        )

        print("=== After score sort ===")
        for c in reranked_results[:20]:
            print(
                c["title"],
                c["genres"],
                c["semantic_score"],
                c["preference_score"],
                c["novelty_score"],
                c["base_score"],
        )

        # Add document_preview before passing to explanation service.
        for result in reranked_results:
            result["document_preview"] = self._make_document_preview(
                result.get("document", "") or ""
            )

        explanation_query = (
            f"Original user query: {query}\n"
            f"Parsed retrieval query: {retrieval_query}"
        )
        
        explanations = self.explanation_service.generate_explanations(
            query=explanation_query,
            recommendations=reranked_results, 
            use_llm_explanation=use_llm_explanation
        )

        recommendations = [
            self._format_recommendation(result, explanation)
            for result, explanation in zip(reranked_results, explanations)
        ]


        latency_ms = (time.perf_counter() - start_time) * 1000 # Convert to milliseconds

        return RecommendResponse(
            user_id=user_id,
            query=query,
            retrieval_query=retrieval_query,
            parsed_intent=parsed_intent,
            intent_provider=self.intent_parser.get_provider_name(use_llm_intent=use_llm_intent),

            top_k=top_k,
            include_watched=include_watched,
            candidate_count=len(raw_candidates),
            filtered_watched_count=filtered_watched_count,
            explanation_provider=self.explanation_service.get_provider_name(use_llm_explanation=use_llm_explanation),

            results=recommendations,
            latency_ms=round(latency_ms, 2),
        )


    def _format_recommendation(self, result: dict[str, Any], explanation: str) -> MovieRecommendation:
        """
        Convert raw vector search result into API response format.
        """
        distance = float(result.get("distance", 0.0))
        final_score = float(result.get("final_score", 0.0))
        semantic_score = float(result.get("semantic_score", 0.0))
        preference_score = float(result.get("preference_score", 0.0))

        novelty_score = float(result.get("novelty_score", 0.0))
        diversity_penalty = float(result.get("diversity_penalty", 0.0))

        title = result.get("title") or "Unknown Title"
        release_year = result.get("release_year")

        if release_year == -1:
            release_year = None

        watched = bool(result.get("watched", False))
        saved = bool(result.get("saved", False))
        preference = result.get("preference")
        if preference not in ("like", "dislike"):
            preference = None
        

        popularity = self._safe_float(result.get("popularity"))
        vote_average = self._safe_float(result.get("vote_average"))
        vote_count = self._safe_int(result.get("vote_count"))


        return MovieRecommendation(
            movie_id=str(result.get("id")),
            title=title,
            release_year=release_year,
            genres=result.get("genres"),
            score=round(final_score, 4),
            distance=round(distance, 4),
            semantic_score=round(semantic_score, 4),
            preference_score=round(preference_score, 4),
            novelty_score=round(novelty_score, 4),
            diversity_penalty=round(diversity_penalty, 4),
            preference=preference,
            watched=watched,
            saved=saved,
            popularity=popularity,
            vote_average=vote_average,
            vote_count=vote_count,
            reason=explanation,
            document_preview=result.get("document_preview", ""),
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
    

    def _safe_float(self, value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    
    def _safe_int(self, value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None