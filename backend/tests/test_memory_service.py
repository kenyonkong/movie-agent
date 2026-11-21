from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.db.models import UserMoviePreference
from app.services.memory_service import MemoryService


def test_memory_summary_reports_current_preference_count() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        db.add(
            UserMoviePreference(
                user_id="user-1",
                movie_id="42",
                title="Movie",
                genres="Drama, Science Fiction",
                preference="like",
                watched=True,
                saved=False,
            )
        )
        db.commit()

        summary = MemoryService().get_memory_summary(
            db=db,
            user_id="user-1",
        )

    assert summary.total_preferences == 1
    assert summary.liked_movies == ["Movie"]
    assert summary.watched_movies == ["Movie"]
    assert summary.liked_genres == {
        "Drama": 1,
        "Science Fiction": 1,
    }

    engine.dispose()
