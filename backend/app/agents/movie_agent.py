import time

from sqlalchemy.orm import Session

from app.agents.state import MovieAgentState # a container for all variables originally in the RecommenderService
from app.agents.tracing import AgentTracer # a tracer for states of the pipeline
from app.db.schemas import RecommendRequest, RecommendResponse
from app.services.explanation_service import ExplanationService # the service for generating explanations for recommendations (llm or local)
from app.services.intent_parser import IntentParserService # the service for parsing user intent (llm or local)
from app.services.memory_service import MemoryService # the service for the user's preference memory, used SQLite
from app.services.recommendation_formatter import RecommendationFormatter # the service for formatting the recommendations to schemas
from app.services.reranker import MovieReranker # the service for re-ranking the recommendations (llm or local)
from app.services.vector_store import MovieVectorStore # the ChromaDB vector store for the movies, 19985 entries


class MovieAgent:
    """
    Coordinates the complete movie recommendation workflow.

    This is a deterministic workflow orchestrator.

    The agent does not let an LLM freely invent movies or decide arbitrary
    tool calls. Every recommendation must originate from the configured
    movie vector store.
    """

    CANDIDATE_MULTIPLIER = 10 # Retrieve this many candidates from vector search before reranking
    MIN_CANDIDATE_POOL = 50 # Always retrieve at least this many candidates for reranking

    def __init__(
        self, 
        intent_parser: IntentParserService | None = None,
        memory_service: MemoryService | None = None,
        vector_store: MovieVectorStore | None = None,
        explanation_service: ExplanationService | None = None,
        formatter: RecommendationFormatter | None = None,
        reranker: MovieReranker | None = None
    ) -> None:
        self.intent_parser = intent_parser or IntentParserService()
        self.memory_service = memory_service or MemoryService()
        self.vector_store = vector_store or MovieVectorStore()
        self.explanation_service = explanation_service or ExplanationService()
        self.formatter = formatter or RecommendationFormatter()
        self.reranker = reranker or MovieReranker()
    

    def recommend(
        self, 
        db: Session, 
        request: RecommendRequest,
    ) -> RecommendResponse:
        """
        Execute one controlled recommendation workflow.
        """
        time_started_at = time.perf_counter()
        tracer = AgentTracer(enabled=request.include_agent_trace)

        state = MovieAgentState(request = request)

        self._validate_tools(state, tracer) # validate the ChromaDB is not empty
        self._parse_intent(state, tracer)
        self._load_memory(db, state, tracer)
        self._retrieve_candidates(state, tracer)
        self._filter_watched_candidates(state, tracer)
        self._heuristic_rerank(state, tracer)
        self._bounded_llm_rerank_placeholder(state, tracer)
        self._generate_explanations(state, tracer)

        format_started_at = tracer.start_step()

        recommendations = self.formatter.format_many(
            candidates=state.final_candidates, 
            explanations=state.explanations
        )

        tracer.complete(
            name="format_response",
            started_at=format_started_at,
            details={
                "recommendation_count": len(recommendations),
            },
        )

        total_latency_ms = (
            time.perf_counter() - time_started_at
        ) * 1000

        return RecommendResponse(
            user_id=request.user_id,
            query=request.query,
            retrieval_query=state.retrieval_query,
            parsed_intent=state.parsed_intent,
            intent_provider=self.intent_parser.get_provider_name(
                use_llm_intent=request.use_llm_intent,
            ),
            top_k=request.top_k,
            include_watched=request.include_watched,
            candidate_count=len(state.raw_candidates),
            filtered_watched_count=(
                state.filtered_watched_count
            ),
            explanation_provider=(
                self.explanation_service.get_provider_name(
                    use_llm_explanation=(
                        request.use_llm_explanations
                    ),
                )
            ),
            results=recommendations,
            latency_ms=round(total_latency_ms, 2),
            agent_trace=tracer.build(),
        )

    
    def _validate_tools(
        self, 
        state: MovieAgentState, 
        tracer: AgentTracer
    ) -> None:
        started_at = tracer.start_step()

        try:
            vector_count = self.vector_store.count()
            if vector_count == 0:
                raise RuntimeError(
                    "The active Chroma collection is empty. "
                    "Build embeddings for the configured provider first."
                )
            
            embedding_service = self.vector_store.embedding_service
            tracer.complete(
                name="validate_tools",
                started_at=started_at,
                details={
                    "vector_store_count": vector_count,
                    "embedding_provider": (
                        embedding_service.provider
                    ),
                    "embedding_model": (
                        embedding_service.model_name
                    ),
                    "chroma_collection": (
                        self.vector_store.collection_name
                    ),
                },
            )

        except Exception as error:
            tracer.fail(
                name="validate_tools",
                started_at=started_at,
                error=error,
            )
            raise
    

    def _parse_intent(
        self, 
        state: MovieAgentState,
        tracer: AgentTracer
    ) -> None:
        started_at = tracer.start_step()

        try:
            parsed_intent = self.intent_parser.parse_intent(
                query=state.request.query,
                use_llm_intent=state.request.use_llm_intent,
            )
            state.parsed_intent = parsed_intent
            state.retrieval_query = (
                parsed_intent.query_rewrite.strip()
                or state.request.query
            )
            tracer.complete(
                name="parse_intent",
                started_at=started_at,
                details={
                    "provider": (
                        self.intent_parser.get_provider_name(
                            state.request.use_llm_intent
                        )
                    ),
                    "reference_movie_count": len(
                        parsed_intent.reference_movies
                    ),
                    "avoid_constraint_count": len(
                        parsed_intent.avoid
                    ),
                    "confidence": parsed_intent.confidence,
                    "query_was_rewritten": (
                        state.retrieval_query.strip()
                        != state.request.query.strip()
                    ),
                },
            )
        except Exception as error:
            tracer.fail(
                name="parse_intent",
                started_at=started_at,
                error=error,
            )
            raise
    

    def _load_memory(
        self,
        db: Session, 
        state: MovieAgentState,
        tracer: AgentTracer
    ) -> None:
        started_at = tracer.start_step()

        try:
            state.user_memory = (
                self.memory_service.get_reranking_memory(db, state.request.user_id)
            )
            tracer.complete(
                name="load_user_memory",
                started_at=started_at,
                details={
                    "liked_genre_count": len(
                        state.user_memory.get(
                            "liked_genres",
                            {},
                        )
                    ),
                    "disliked_genre_count": len(
                        state.user_memory.get(
                            "disliked_genres",
                            {},
                        )
                    ),
                    "watched_movie_count": len(
                        state.user_memory.get(
                            "watched_movie_ids",
                            set(),
                        )
                    ),
                    "saved_movie_count": len(
                        state.user_memory.get(
                            "saved_movie_ids",
                            set(),
                        )
                    ),
                },
            )

        except Exception as error:
            tracer.fail(
                name="load_user_memory",
                started_at=started_at,
                error=error,
            )
            raise
    

    def _retrieve_candidates(
        self,
        state: MovieAgentState,
        tracer: AgentTracer
    ) -> None:
        started_at = tracer.start_step()

        try:
            candidate_k = max(state.request.top_k * self.CANDIDATE_MULTIPLIER, 
                              self.MIN_CANDIDATE_POOL)
            state.raw_candidates = self.vector_store.search(
                query=state.retrieval_query,
                top_k=candidate_k
            )
            tracer.complete(
                name="retrieve_candidates",
                started_at=started_at,
                details={
                    "requested_candidate_count": candidate_k,
                    "returned_candidate_count": len(
                        state.raw_candidates
                    ),
                    "collection": (
                        self.vector_store.collection_name
                    ),
                },
            )

        except Exception as error:
            tracer.fail(
                name="retrieve_candidates",
                started_at=started_at,
                error=error,
            )
            raise
    

    def _filter_watched_candidates(
        self, 
        state: MovieAgentState,
        tracer: AgentTracer
    ) -> None:
        started_at = tracer.start_step()

        try:
            state.filtered_candidates, state.filtered_watched_count = self.reranker.filter_watched_candidates(
                candidates=state.raw_candidates,
                user_memory=state.user_memory,
                include_watched=state.request.include_watched
            )

            enough_filtered_candidates = (
                len(state.filtered_candidates) >= state.request.top_k
            )

            if enough_filtered_candidates:
                state.candidates_for_reranking = state.filtered_candidates
            else:
                state.candidates_for_reranking = state.raw_candidates
                state.watched_filter_fallback_used = True

            tracer.complete(
                name="filter_watched_candidates",
                started_at=started_at,
                details={
                    "include_watched": (
                        state.request.include_watched
                    ),
                    "filtered_watched_count": (
                        state.filtered_watched_count
                    ),
                    "remaining_candidate_count": len(
                        state.filtered_candidates
                    ),
                    "fallback_to_raw_candidates": (
                        state.watched_filter_fallback_used
                    ),
                },
            )

        except Exception as error:
            tracer.fail(
                name="filter_watched_candidates",
                started_at=started_at,
                error=error,
            )
            raise
    

    def _heuristic_rerank(
        self, 
        state: MovieAgentState, 
        tracer: AgentTracer
    ) -> None:
        started_at = tracer.start_step()

        try:
            # Retrieve more than final top_k here so Day 16 can let the
            # bounded LLM reranker inspect a controlled shortlist.
            heuristic_top_k = min(
                max(state.request.top_k * 3, 10),
                len(state.candidates_for_reranking),
            )

            state.heuristic_candidates = (
                self.reranker.rerank(
                    candidates=state.candidates_for_reranking,
                    user_memory=state.user_memory,
                    top_k=heuristic_top_k,
                )
            )

            tracer.complete(
                name="heuristic_rerank",
                started_at=started_at,
                details={
                    "input_candidate_count": len(
                        state.candidates_for_reranking
                    ),
                    "shortlist_count": len(
                        state.heuristic_candidates
                    ),
                    "requested_final_top_k": (
                        state.request.top_k
                    ),
                    "semantic_weight": (
                        self.reranker.SEMANTIC_WEIGHT
                    ),
                    "preference_weight": (
                        self.reranker.PREFERENCE_WEIGHT
                    ),
                    "novelty_weight": (
                        self.reranker.NOVELTY_WEIGHT
                    ),
                    "diversity_weight": (
                        self.reranker.DIVERSITY_WEIGHT
                    ),
                },
            )

        except Exception as error:
            tracer.fail(
                name="heuristic_rerank",
                started_at=started_at,
                error=error,
            )
            raise
        

    def _bounded_llm_rerank_placeholder(
        self,
        state: MovieAgentState,
        tracer: AgentTracer,
    ) -> None:
        """
        Day 15 deliberately does not implement LLM reranking.

        Until Day 16, take the first top_k results from the heuristic
        shortlist. This creates an explicit extension point.
        """
        state.final_candidates = (
            state.heuristic_candidates[
                : state.request.top_k
            ]
        )

        tracer.skip(
            name="bounded_llm_rerank",
            reason=(
                "Bounded LLM reranking is disabled until Day 16. "
                "Using heuristic ranking order."
            ),
            details={
                "available_shortlist_count": len(
                    state.heuristic_candidates
                ),
                "selected_count": len(
                    state.final_candidates
                ),
            },
        )
        
    def _generate_explanations(
        self, 
        state: MovieAgentState,
        tracer: AgentTracer,
    ) -> None:
        started_at = tracer.start_step()

        try:
            self.formatter.prepare_document_previews(
                state.final_candidates
            )
            explanation_query = (
                f"Original user query: "
                f"{state.request.query}\n"
                f"Parsed retrieval query: "
                f"{state.retrieval_query}"
            )

            state.explanations = self.explanation_service.generate_explanations(
                query=explanation_query,
                recommendations=state.final_candidates, 
                use_llm_explanation=state.request.use_llm_explanations
            )
            tracer.complete(
                name="generate_explanations",
                started_at=started_at,
                details={
                    "provider": (
                        self.explanation_service
                        .get_provider_name(
                            state.request
                            .use_llm_explanations
                        )
                    ),
                    "candidate_count": len(
                        state.final_candidates
                    ),
                    "explanation_count": len(
                        state.explanations
                    ),
                },
            )

        except Exception as error:
            tracer.fail(
                name="generate_explanations",
                started_at=started_at,
                error=error,
            )
            raise
        
