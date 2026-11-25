from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MovieReview(Base):
    __tablename__ = "movie_reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_movie_review"),
        CheckConstraint("rating BETWEEN 1 AND 10", name="ck_movie_review_rating"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    movie_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(512))
    rating: Mapped[int]
    body: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DoubanReviewSource(Base):
    __tablename__ = "douban_review_sources"

    review_id: Mapped[int] = mapped_column(
        ForeignKey("movie_reviews.id", ondelete="CASCADE"), primary_key=True
    )
    record_id: Mapped[str] = mapped_column(String(128))
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    original_body: Mapped[str] = mapped_column(Text)
    english_body: Mapped[str | None] = mapped_column(Text)


class UserMoviePreference(Base):
    """
    Stores one current preference state per user/movie pair.

    This is not an append-only event log.

    For each (user_id, movie_id), there should be at most one row.

    State:
    - preference: "like", "dislike", or None
    - watched: independent boolean flag
    - saved: independent boolean flag
    """

    __tablename__ = "user_movie_preferences"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="uq_user_movie_preference",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(String(128), index=True)
    movie_id: Mapped[str] = mapped_column(String(128), index=True)

    title: Mapped[str] = mapped_column(String(512))

    query: Mapped[str | None] = mapped_column(Text, nullable=True) # Original user query that led to this recommendation
    genres: Mapped[str | None] = mapped_column(Text, nullable=True) # Genres of the movie at time of feedback
    score: Mapped[float | None] = mapped_column(Float, nullable=True) # Relevance score of the recommendation at time of feedback

    # "like", "dislike", or None
    preference: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Independent boolean flags for watched and saved states
    watched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True, 
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False
    )
