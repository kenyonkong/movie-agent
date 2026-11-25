from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DoubanReviewSource, MovieReview
from app.services.taste_profile import TasteProfile, saved_profile

router = APIRouter(prefix="/users/{user_id}/taste-profile", tags=["taste profile"])


@router.get("", response_model=TasteProfile | None)
def get_taste_profile(user_id: str, db: Annotated[Session, Depends(get_db)]):
    profile = saved_profile(db, user_id)
    if profile and profile.history:
        marked = func.coalesce(DoubanReviewSource.marked_at, MovieReview.updated_at)
        rows = db.execute(select(MovieReview.id, MovieReview.body, marked)
            .outerjoin(DoubanReviewSource, DoubanReviewSource.review_id == MovieReview.id)
            .where(MovieReview.user_id == user_id).order_by(marked, MovieReview.id))
        profile.is_current = [(key, body, when.date()) for key, body, when in rows] == [
            (r.review_id, r.original_body, r.reviewed_on) for r in profile.reviews
        ]
    return profile
