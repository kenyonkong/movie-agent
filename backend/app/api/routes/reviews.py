from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.movies import movie_catalog
from app.db.models import DoubanReviewSource, MovieReview, TasteProfileSnapshot, UserMoviePreference
from app.services.taste_history import refresh_after_save
from app.db.schemas import MovieReviewResponse, MovieReviewWrite, MovieSearchItem

router = APIRouter(prefix="/users/{user_id}/reviews", tags=["reviews"])
Identifier = Annotated[str, Path(min_length=1, max_length=128)]
Database = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[MovieReviewResponse])
def list_reviews(user_id: Identifier, db: Database) -> list[MovieReviewResponse]:
    rows = db.execute(
        select(MovieReview, UserMoviePreference.watched, DoubanReviewSource)
        .outerjoin(DoubanReviewSource, DoubanReviewSource.review_id == MovieReview.id)
        .outerjoin(
            UserMoviePreference,
            and_(
                UserMoviePreference.user_id == MovieReview.user_id,
                UserMoviePreference.movie_id == MovieReview.movie_id,
            ),
        )
        .where(MovieReview.user_id == user_id)
        .order_by(
            func.coalesce(DoubanReviewSource.marked_at, MovieReview.updated_at).desc(),
            MovieReview.id.desc(),
        )
    ).all()
    movies = movie_catalog.get_movies_by_id({review.movie_id for review, _, _ in rows})
    return [
        review_response(review, movies.get(review.movie_id), bool(watched), source)
        for review, watched, source in rows
    ]


@router.put("/{movie_id}", response_model=MovieReviewResponse)
def save_review(
    user_id: Identifier, movie_id: Identifier, request: MovieReviewWrite, db: Database,
    background_tasks: BackgroundTasks,
) -> MovieReviewResponse:
    movie = movie_catalog.get_movies_by_id({movie_id}).get(movie_id)
    for attempt in range(2):
        try:
            review = persist_review(db, user_id, movie_id, request)
            snapshot = db.get(TasteProfileSnapshot, user_id)
            if snapshot and snapshot.document.get("history"):
                background_tasks.add_task(refresh_after_save, db.get_bind(), user_id, snapshot.document["model"])
            return review_response(
                review, movie, watched=True, source=db.get(DoubanReviewSource, review.id)
            )
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
    # Keep the existing SQLite scale so older review rows stay compatible.
    review.rating = request.rating * 2
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
    review: MovieReview, movie: MovieSearchItem | None, watched: bool,
    source: DoubanReviewSource | None = None,
) -> MovieReviewResponse:
    return MovieReviewResponse(
        movie_id=review.movie_id,
        title=movie.title if source and movie else review.title,
        rating=(review.rating + 1) // 2,
        body=review.body,
        updated_at=review.updated_at,
        poster_url=movie.poster_url if movie else None,
        watched=watched,
        marked_date=source.marked_at.date() if source else None,
        review_en=source.english_body if source and review.body == source.original_body else None,
    )
