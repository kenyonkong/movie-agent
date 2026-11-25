from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DoubanReviewSource, MovieReview, TasteProfileSnapshot
from app.services.taste_profile import TasteProfile

router = APIRouter(prefix="/users/{user_id}/taste-profile", tags=["taste profile"])


@router.get("", response_model=TasteProfile | None)
def get_taste_profile(user_id: str, db: Annotated[Session, Depends(get_db)]):
    snapshot = db.get(TasteProfileSnapshot, user_id)
    if snapshot is None:
        return None
    profile = TasteProfile.model_validate(snapshot.document)
    missing = {review.review_id: review for review in profile.reviews if review.original_body is None}
    if missing:
        # Recover the full text used by older builds, even if the review was edited later.
        rows = db.execute(
            select(MovieReview.id, MovieReview.body, DoubanReviewSource)
            .outerjoin(DoubanReviewSource, DoubanReviewSource.review_id == MovieReview.id)
            .where(MovieReview.user_id == user_id, MovieReview.id.in_(missing))
        )
        for review_id, body, source in rows:
            review = missing[review_id]
            if source and review.display_body == source.english_body:
                review.original_body = source.original_body
            elif review.display_body == body or (source and review.display_body == source.original_body):
                review.original_body = review.display_body
    return profile
