from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class UserFeedback(Base):
    """
    Stores explicit user feedback on recommended movies.

    Actions:
    - like
    - dislike
    - watched
    - save
    """

    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(String(128), index=True)
    movie_id: Mapped[str] = mapped_column(String(128), index=True)

    title: Mapped[str] = mapped_column(String(512))
    action: Mapped[str] = mapped_column(String(32), index=True) # like, dislike, watched, save

    query: Mapped[str | None] = mapped_column(Text, nullable=True) # Original user query that led to this recommendation
    genres: Mapped[str | None] = mapped_column(Text, nullable=True) # Genres of the movie at time of feedback

    score: Mapped[float | None] = mapped_column(Float, nullable=True) # Relevance score of the recommendation at time of feedback

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True
    )