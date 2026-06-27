from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import RecommendRequest, RecommendResponse
from app.agents.movie_agent import MovieAgent

router = APIRouter(prefix="/recommend", tags=["recommendation"])

movie_agent = MovieAgent() # global recommender instance avoids repeated initialization overhead.

@router.post("", response_model=RecommendResponse)
def recommend_movies(
    request: RecommendRequest,
    db: Session = Depends(get_db)
) -> RecommendResponse:
    """
    Recommend movies from a natural-language user query.

    Development version:
    - Uses semantic vector search
    - Returns top-k candidates
    - Includes simple non-LLM explanations
    - Optionally uses LLM-generated explanations

    Day 15: Run the controlled MovieAgent recommendation workflow.
    """
    try:
        return movie_agent.recommend(
            db=db,
            request=request,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unexpected MovieAgent error: "
                f"{error}"
            ),
        ) from error
    

@router.get("/debug")
def recommend_debug() -> dict:
    embedding_service = (
        movie_agent.vector_store.embedding_service
    )

    return {
        "agent": {
            "name": "movie_agent",
            "version": "day16",
            "workflow": (
                "deterministic_tool_orchestration"
            ),
        },
        "vector_store": {
            "count": (
                movie_agent.vector_store.count()
            ),
            "collection": (
                movie_agent.vector_store
                .collection_name
            ),
            "embedding_provider": (
                embedding_service.provider
            ),
            "embedding_model": (
                embedding_service.model_name
            ),
        },
        "tools": {
            "intent_parser": {
                "provider": (
                    movie_agent.intent_parser
                    .provider
                ),
                "model": (
                    movie_agent.intent_parser
                    .model
                ),
            },
            "constraint_engine": {
                "enabled_by_default": True,
                "supported_fields": [
                    "director",
                    "cast",
                    "genres",
                    "excluded genres",
                    "original language",
                    "runtime",
                    "release year",
                    "vote average",
                    "vote count",
                ],
                "strategy": (
                    "chroma_pushdown_plus_python_validation"
                ),
            },
            "bounded_llm_reranker": {
                "provider": (
                    movie_agent.llm_reranker
                    .provider
                ),
                "model": (
                    movie_agent.llm_reranker
                    .model
                ),
                "shortlist_size": (
                    movie_agent.llm_reranker
                    .shortlist_size
                ),
            },
            "explanation_service": {
                "provider": (
                    movie_agent
                    .explanation_service
                    .provider
                ),
                "model": (
                    movie_agent
                    .explanation_service
                    .model
                ),
            },
        },
    }