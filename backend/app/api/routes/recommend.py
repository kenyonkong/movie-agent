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
    """
    Debug endpoint to check if the recommender service is working without needing a full request body.
    """
    return {
        "vector_store_count": recommender.vector_store.count(),
        "message": "Recommendation service is ready.",
        "reranked": "enabled",
        "watched_filtering": "configurable",
        "explanation_provider": recommender.explanation_service.provider,
        "explanation_model": recommender.explanation_service.model,
    }