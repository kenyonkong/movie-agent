"""Import matched Douban reviews from a prepared JSON file."""

import argparse
import json
from collections import Counter
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, create_db_tables
from app.db.models import DoubanReviewSource, MovieReview, UserMoviePreference
from app.db.schemas import MovieReviewWrite


class PreparedReview(BaseModel):
    record_id: str = Field(min_length=1, max_length=128)
    movie_id: str | None = Field(min_length=1, max_length=128)
    match_status: str
    title: str
    rating: Annotated[int, Field(strict=True, ge=1, le=5)]
    review_original: str
    review_en: str | None
    marked_date: date


class PreparedExport(BaseModel):
    source: Literal["douban"]
    records: list[PreparedReview]


def import_reviews(db: Session, source: PreparedExport, user_id: str) -> Counter:
    stats = Counter(imported=0, existing=0, unmatched=0)
    reviews = set(db.scalars(select(MovieReview.movie_id).filter_by(user_id=user_id)))
    preferences = {
        preference.movie_id: preference
        for preference in db.scalars(select(UserMoviePreference).filter_by(user_id=user_id))
    }
    seen_ids: set[str] = set()
    seen_movies: set[str] = set()

    for record in source.records:
        if record.record_id in seen_ids:
            raise ValueError("The export contains a duplicate Douban record ID.")
        seen_ids.add(record.record_id)
        if record.match_status != "matched" or not record.movie_id:
            stats["unmatched"] += 1
            continue
        if record.movie_id in seen_movies:
            raise ValueError("Multiple Douban records match the same catalog movie.")
        seen_movies.add(record.movie_id)
        if record.movie_id in reviews:
            stats["existing"] += 1
            continue

        review_data = MovieReviewWrite(
            title=record.title, rating=record.rating, body=record.review_original,
        )
        marked_at = datetime.combine(record.marked_date, time.min, tzinfo=timezone.utc)
        review = MovieReview(
            user_id=user_id,
            movie_id=record.movie_id,
            title=review_data.title,
            rating=review_data.rating * 2,
            body=record.review_original,
            updated_at=marked_at,
        )
        db.add(review)
        db.flush()
        db.add(DoubanReviewSource(
            review_id=review.id,
            record_id=record.record_id,
            marked_at=marked_at,
            original_body=record.review_original,
            english_body=record.review_en,
        ))
        preference = preferences.get(record.movie_id)
        if preference is None:
            preference = UserMoviePreference(
                user_id=user_id, movie_id=record.movie_id, title=review_data.title,
            )
            db.add(preference)
        preference.watched = True
        stats["imported"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--user-id", default="demo_user")
    args = parser.parse_args()
    if not args.user_id.strip() or len(args.user_id) > 128:
        parser.error("A nonblank user ID of at most 128 characters is required.")
    source = PreparedExport.model_validate(json.loads(args.source.read_text(encoding="utf-8-sig")))
    create_db_tables()
    with SessionLocal.begin() as db:
        stats = import_reviews(db, source, args.user_id)
    print(f"Imported {stats['imported']}; skipped {stats['existing']} existing and {stats['unmatched']} unmatched.")


if __name__ == "__main__":
    main()
