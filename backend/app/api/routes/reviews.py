from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.movies import movie_catalog
from app.db.models import MovieReview, UserMoviePreference
from app.db.schemas import MovieReviewResponse, MovieReviewWrite

router = APIRouter(prefix="/users/{user_id}/reviews", tags=["reviews"])
Identifier = Annotated[str, Path(min_length=1, max_length=128)]
Database = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[MovieReviewResponse])
def list_reviews(user_id: Identifier, db: Database) -> list[MovieReviewResponse]:
    rows = db.execute(
        select(MovieReview, UserMoviePreference.watched)
        .outerjoin(
            UserMoviePreference,
            and_(
                UserMoviePreference.user_id == MovieReview.user_id,
                UserMoviePreference.movie_id == MovieReview.movie_id,
            ),
        )
        .where(MovieReview.user_id == user_id)
        .order_by(MovieReview.updated_at.desc(), MovieReview.id.desc())
    ).all()
    posters = movie_catalog.get_posters({review.movie_id for review, _ in rows})
    return [
        review_response(review, posters.get(review.movie_id), bool(watched))
        for review, watched in rows
    ]


@router.put("/{movie_id}", response_model=MovieReviewResponse)
def save_review(
    user_id: Identifier, movie_id: Identifier, request: MovieReviewWrite, db: Database
) -> MovieReviewResponse:
    poster = movie_catalog.get_posters({movie_id}).get(movie_id)
    for attempt in range(2):
        try:
            review = persist_review(db, user_id, movie_id, request)
            return review_response(review, poster, watched=True)
        except IntegrityError:
            # A concurrent request may have created either row first.
            db.rollback()
            if attempt == 1:
                raise
    raise RuntimeError("Review save did not complete")


def persist_review(
    db: Session, user_id: str, movie_id: str, request: MovieReviewWrite,
) -> MovieReview:
    review = db.scalar(select(MovieReview).filter_by(user_id=user_id, movie_id=movie_id))
    if review is None:
        review = MovieReview(user_id=user_id, movie_id=movie_id)
        db.add(review)
    review.title = request.title
    review.rating = request.rating
    review.body = request.body
    review.updated_at = datetime.now(timezone.utc)

    preference = db.scalar(
        select(UserMoviePreference).filter_by(user_id=user_id, movie_id=movie_id)
    )
    if preference is None:
        preference = UserMoviePreference(user_id=user_id, movie_id=movie_id, title=request.title)
        db.add(preference)
    preference.watched = True
    db.commit()
    db.refresh(review)
    return review


def review_response(
    review: MovieReview, poster_url: str | None, watched: bool,
) -> MovieReviewResponse:
    return MovieReviewResponse(
        movie_id=review.movie_id,
        title=review.title,
        rating=review.rating,
        body=review.body,
        updated_at=review.updated_at,
        poster_url=poster_url,
        watched=watched,
    )
