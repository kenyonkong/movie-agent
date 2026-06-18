from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import RecommendRequest, RecommendResponse
from app.services.recommender import RecommenderService

router = APIRouter(prefix="/recommend", tags=["recommendation"])

recommender = RecommenderService() # global recommender instance avoids repeated initialization overhead.

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
    """
    try:
        return recommender.recommend(
            db=db,
            user_id=request.user_id,
            query=request.query,
            top_k=request.top_k,
            include_watched=request.include_watched,
            use_llm_explanation=request.use_llm_explanations,
            use_llm_intent=request.use_llm_intent,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected recommendation error: {error}",
        ) from error
    

@router.get("/debug")
def recommend_debug() -> dict:
    return {
        "vector_store_count": recommender.vector_store.count(),
        "embedding_provider": (
            recommender.vector_store
            .embedding_service
            .provider
        ),
        "embedding_model": (
            recommender.vector_store
            .embedding_service
            .model_name
        ),
        "embedding_dimensions": (
            recommender.vector_store
            .embedding_service
            .actual_dimension
        ),
        "chroma_collection": (
            recommender.vector_store.collection_name
        ),
        "intent_parser_provider": (
            recommender.intent_parser.provider
        ),
        "explanation_provider": (
            recommender.explanation_service.provider
        ),
        "reranking": "enabled",
    }