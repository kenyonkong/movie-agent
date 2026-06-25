import statistics
import time
from typing import Any

from app.agents.movie_agent import MovieAgent
from app.db.database import SessionLocal
from app.db.schemas import RecommendRequest
from app.evaluation.catalog import (
    CatalogIndex,
    split_csv,
)
from app.evaluation.models import (
    EvaluationConfig,
    EvaluationMovie,
    EvaluationQuery,
    EvaluationRun,
)
from app.services.bounded_llm_reranker import (
    BoundedLLMReranker,
)
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.intent_parser import (
    IntentParserService,
)
from app.services.vector_store import (
    MovieVectorStore,
)


def first_not_none(
    *values: Any,
) -> Any:
    for value in values:
        if value is not None:
            return value

    return None


class EvaluationPipeline:
    """
    One reusable pipeline for one evaluation configuration.

    Expensive services are constructed once and reused across queries.
    """

    def __init__(
        self,
        config: EvaluationConfig,
        catalog: CatalogIndex,
    ) -> None:
        self.config = config
        self.catalog = catalog

        self.embedding_service = (
            EmbeddingService(
                provider=(
                    config.embedding_provider
                ),
                model_name=(
                    config.embedding_model
                ),
                dimensions=(
                    config.embedding_dimensions
                ),
            )
        )

        self.vector_store = MovieVectorStore(
            embedding_service=(
                self.embedding_service
            )
        )

        if self.vector_store.count() == 0:
            raise RuntimeError(
                "The configured Chroma collection "
                f"is empty: "
                f"{self.vector_store.collection_name}"
            )

        self.intent_parser = IntentParserService(
            provider=config.intent_provider,
            model=config.intent_model,
        )

        self.llm_reranker = (
            BoundedLLMReranker(
                provider=(
                    config.llm_reranker_provider
                ),
                model=(
                    config.llm_reranker_model
                ),
            )
        )

        self.agent: MovieAgent | None = None

        if config.mode == "agent":
            self.agent = MovieAgent(
                vector_store=self.vector_store,
                intent_parser=self.intent_parser,
                llm_reranker=(
                    self.llm_reranker
                ),
            )

    def run(
        self,
        query: EvaluationQuery,
    ) -> EvaluationRun:
        latencies: list[float] = []

        final_payload: dict[str, Any] | None = None

        for _ in range(
            self.config.latency_repeats
        ):
            started_at = time.perf_counter()

            payload = self._execute_once(query)

            latency_ms = (
                time.perf_counter()
                - started_at
            ) * 1000

            latencies.append(latency_ms)
            final_payload = payload

        if final_payload is None:
            raise RuntimeError(
                "Evaluation pipeline produced no payload."
            )

        return EvaluationRun(
            config_name=self.config.name,
            query_id=query.id,
            query=query.query,
            retrieval_query=(
                final_payload[
                    "retrieval_query"
                ]
            ),
            embedding_identifier=(
                self.embedding_service
                .model_identifier
            ),
            intent_provider=(
                final_payload.get(
                    "intent_provider"
                )
            ),
            reranker_provider=(
                final_payload.get(
                    "reranker_provider"
                )
            ),
            latency_ms=round(
                statistics.median(
                    latencies
                ),
                2,
            ),
            input_tokens=int(
                final_payload.get(
                    "input_tokens",
                    0,
                )
            ),
            output_tokens=int(
                final_payload.get(
                    "output_tokens",
                    0,
                )
            ),
            fallback_used=bool(
                final_payload.get(
                    "fallback_used",
                    False,
                )
            ),
            results=final_payload[
                "results"
            ],
            trace=final_payload.get(
                "trace"
            ),
        )

    def _execute_once(
        self,
        query: EvaluationQuery,
    ) -> dict[str, Any]:
        if (
            self.config.mode
            == "raw_retrieval"
        ):
            return self._run_raw_retrieval(
                query
            )

        if (
            self.config.mode
            == "intent_retrieval"
        ):
            return self._run_intent_retrieval(
                query
            )

        if self.config.mode == "agent":
            return self._run_agent(query)

        raise ValueError(
            f"Unsupported mode: "
            f"{self.config.mode}"
        )

    # Only the ChromaDB semantic search
    def _run_raw_retrieval(
        self,
        query: EvaluationQuery,
    ) -> dict[str, Any]:
        raw_results = self.vector_store.search(
            query=query.query,
            top_k=query.top_k,
        )

        return {
            "retrieval_query": query.query,
            "intent_provider": None,
            "reranker_provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "fallback_used": False,
            "trace": None,
            "results": self._normalize_results(
                raw_results
            ),
        }

    # LLM Parse Intent + ChromaDB semantic search
    def _run_intent_retrieval(
        self,
        query: EvaluationQuery,
    ) -> dict[str, Any]:
        parsed_intent = (
            self.intent_parser.parse_intent(
                query=query.query,
                use_llm_intent=(
                    self.config
                    .use_llm_intent
                ),
            )
        )

        retrieval_query = (
            parsed_intent.query_rewrite.strip()
            or query.query
        )

        raw_results = self.vector_store.search(
            query=retrieval_query,
            top_k=query.top_k,
        )

        return {
            "retrieval_query": (
                retrieval_query
            ),
            "intent_provider": (
                self.intent_parser
                .get_provider_name(
                    self.config
                    .use_llm_intent
                )
            ),
            "reranker_provider": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "fallback_used": False,
            "trace": None,
            "results": self._normalize_results(
                raw_results
            ),
        }

    def _run_agent(
        self,
        query: EvaluationQuery,
    ) -> dict[str, Any]:
        if self.agent is None:
            raise RuntimeError(
                "Agent pipeline was not initialized."
            )

        request = RecommendRequest(
            user_id=query.user_id,
            query=query.query,
            top_k=query.top_k,
            include_watched=False,
            use_llm_intent=(
                self.config.use_llm_intent
            ),
            use_llm_reranker=(
                self.config
                .use_llm_reranker
            ),
            # Explanation generation does not change
            # ranking and would make evaluation slower.
            use_llm_explanations=False,
            include_agent_trace=True,
        )

        db = SessionLocal()

        try:
            response = self.agent.recommend(
                db=db,
                request=request,
            )
        finally:
            db.close()

        trace_dict = (
            response.agent_trace.model_dump()
            if response.agent_trace
            else None
        )

        input_tokens = 0
        output_tokens = 0

        if trace_dict:
            for step in trace_dict.get(
                "steps",
                [],
            ):
                details = step.get(
                    "details",
                    {},
                )

                input_tokens += int(
                    details.get(
                        "input_tokens",
                        0,
                    )
                    or 0
                )

                output_tokens += int(
                    details.get(
                        "output_tokens",
                        0,
                    )
                    or 0
                )

        return {
            "retrieval_query": (
                response.retrieval_query
            ),
            "intent_provider": (
                response.intent_provider
            ),
            "reranker_provider": (
                response.reranker_provider
            ),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "fallback_used": (
                response
                .reranker_fallback_used
            ),
            "trace": trace_dict,
            "results": self._normalize_results(
                response.results
            ),
        }

    def _normalize_results(
        self,
        raw_results: list[Any],
    ) -> list[EvaluationMovie]:
        normalized: list[
            EvaluationMovie
        ] = []

        for rank, item in enumerate(
            raw_results,
            start=1,
        ):
            if hasattr(item, "model_dump"):
                data = item.model_dump()
            else:
                data = dict(item)

            movie_id = str(
                first_not_none(
                    data.get("movie_id"),
                    data.get("id"),
                    "",
                )
            )

            title = str(
                data.get("title")
                or ""
            )

            catalog_record = (
                self.catalog.get(
                    movie_id=movie_id,
                    title=title,
                )
            )

            genres_text = first_not_none(
                data.get("genres"),
                catalog_record.get(
                    "genres"
                ),
                "",
            )

            cast_text = first_not_none(
                data.get("cast"),
                catalog_record.get(
                    "cast"
                ),
                "",
            )

            director = str(
                first_not_none(
                    data.get("director"),
                    catalog_record.get(
                        "director"
                    ),
                    "",
                )
            )

            popularity = float(
                first_not_none(
                    data.get(
                        "popularity"
                    ),
                    catalog_record.get(
                        "popularity"
                    ),
                    0.0,
                )
                or 0.0
            )

            release_year_value = (
                first_not_none(
                    data.get(
                        "release_year"
                    ),
                    catalog_record.get(
                        "release_year"
                    ),
                )
            )

            runtime_value = (
                first_not_none(
                    data.get("runtime"),
                    catalog_record.get(
                        "runtime"
                    ),
                )
            )

            semantic_score = (
                first_not_none(
                    data.get(
                        "semantic_score"
                    ),
                )
            )

            final_score = (
                first_not_none(
                    data.get("score"),
                    data.get(
                        "final_score"
                    ),
                )
            )

            normalized.append(
                EvaluationMovie(
                    movie_id=movie_id,
                    title=title,
                    rank=rank,
                    release_year=(
                        int(
                            release_year_value
                        )
                        if release_year_value
                        is not None
                        else None
                    ),
                    genres=split_csv(
                        genres_text
                    ),
                    director=director,
                    cast=split_csv(
                        cast_text
                    ),
                    runtime=(
                        int(runtime_value)
                        if runtime_value
                        not in {
                            None,
                            "",
                            0,
                        }
                        else None
                    ),
                    original_language=str(
                        first_not_none(
                            data.get(
                                "original_language"
                            ),
                            catalog_record.get(
                                "original_language"
                            ),
                            "",
                        )
                    ),
                    popularity=popularity,
                    vote_average=float(
                        first_not_none(
                            data.get(
                                "vote_average"
                            ),
                            catalog_record.get(
                                "vote_average"
                            ),
                            0.0,
                        )
                        or 0.0
                    ),
                    vote_count=int(
                        first_not_none(
                            data.get(
                                "vote_count"
                            ),
                            catalog_record.get(
                                "vote_count"
                            ),
                            0,
                        )
                        or 0
                    ),
                    semantic_score=(
                        float(
                            semantic_score
                        )
                        if semantic_score
                        is not None
                        else None
                    ),
                    final_score=(
                        float(final_score)
                        if final_score
                        is not None
                        else None
                    ),
                    heuristic_rank=(
                        int(
                            data[
                                "heuristic_rank"
                            ]
                        )
                        if data.get(
                            "heuristic_rank"
                        )
                        is not None
                        else None
                    ),
                    llm_rank=(
                        int(
                            data[
                                "llm_rank"
                            ]
                        )
                        if data.get(
                            "llm_rank"
                        )
                        is not None
                        else None
                    ),
                    catalog_novelty=(
                        self.catalog
                        .novelty_score(
                            popularity
                        )
                    ),
                )
            )

        return normalized