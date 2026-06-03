from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import FeedbackRequest, FeedbackResponse, UserMemorySummary
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/feedback", tags=["feedback"])
memory_service = MemoryService()

@router.post("/", response_model=FeedbackResponse)
def save_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """
    Save one user feedback to the database.

    This is a simple endpoint that allows the frontend to send user feedback
    (like/dislike/watched/save) for a recommended movie. The feedback is stored
    in the database and can be used later for personalized reranking.
    """
    try:
        return memory_service.save_feedback(db, request)

    except Exception as error:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save feedback: {error}"
        ) from error
    

@router.get("/{user_id}", response_model=list[FeedbackResponse])
def get_recent_feedback(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> list[FeedbackResponse]:
    """
    Return recent feedback events for one user.

    This can be used by the frontend to display a history of user interactions
    or by the recommender to understand recent user preferences.
    """
    return memory_service.get_recent_feedback(
        db=db,
        user_id=user_id,
        limit=limit,
    )


@router.get("/{user_id}/summary", response_model=UserMemorySummary)
def get_memory_summary(
    user_id: str,
    db: Session = Depends(get_db),
) -> UserMemorySummary:
    """
    Return a summary of the user's feedback memory.

    This endpoint provides an aggregated view of the user's preferences, such as
    liked movies and genres. It can be used by the frontend to show a user profile
    or by the recommender for personalized reranking.
    """
    return memory_service.get_memory_summary(db=db, user_id=user_id)
