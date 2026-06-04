from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import UserMoviePreference
from app.db.schemas import (FeedbackRequest, UserMoviePreferenceResponse, UserMemorySummary,)


class MemoryService:
    """
    Service for saving and reading user feedback memory.

    For Day 6, this service only stores and summarizes explicit feedback.
    Later, the recommender will use this memory for personalized reranking.
    """

    VALID_ACTIONS = {"like", "dislike", "watched", "save"}

    def save_feedback(
        self,
        db: Session,
        request: FeedbackRequest,
    ) -> UserMoviePreferenceResponse:
        """
        Upsert one current preference state for a user/movie pair.

        Behavior:
        - like sets preference = "like"
        - dislike sets preference = "dislike"
        - watched sets watched = True
        - save sets saved = True

        Repeated clicks do not create duplicate rows.
        """
        preference = self._get_existing_preference(
            db = db, 
            user_id = request.user_id, 
            movie_id = request.movie_id)
        
        now = datetime.now(timezone.utc)
        if preference is None:
            # Create new preference
            preference = UserMoviePreference(
                user_id=request.user_id,
                movie_id=request.movie_id,
                title=request.title,
                query=request.query,
                genres=request.genres,
                score=request.score,
                preference=None,
                watched=False,
                saved=False,
                created_at=now,
                updated_at=now,
            )
            db.add(preference)
        
        # Always refresh display/context metadata with the latest recommendation context.
        preference.title = request.title
        preference.query = request.query
        preference.genres = request.genres
        preference.score = request.score
        preference.updated_at = now
    
        if request.action == "like":
            preference.preference = "like"

        elif request.action == "dislike":
            preference.preference = "dislike"

        elif request.action == "watched":
            preference.watched = True

        elif request.action == "save":
            preference.saved = True

        else:
            raise ValueError(f"Unsupported feedback action: {request.action}")

        db.commit()
        db.refresh(preference)

        return self._to_preference_response(preference)

    def get_user_preferences(
        self,
        db: Session,
        user_id: str,
        limit: int = 10,
    ) -> list[UserMoviePreferenceResponse]:
        """
        Return recent feedback events for one user.
        """
        statement = (
            select(UserMoviePreference)
            .where(UserMoviePreference.user_id == user_id)
            .order_by(desc(UserMoviePreference.updated_at))
            .limit(limit)
        )
        
        feedbacks = db.execute(statement).scalars().all()
        return [self._to_preference_response(feedback) for feedback in feedbacks]
    

    def get_memory_summary(
        self,
        db: Session,
        user_id: str,
    ) -> UserMemorySummary:
        """
        Return a summary of the user's feedback history, including liked/disliked movies and genres.
        """
        statement = (
            select(UserMoviePreference)
            .where(UserMoviePreference.user_id == user_id)
            .order_by(desc(UserMoviePreference.updated_at))
        )
        
        preference_items = db.execute(statement).scalars().all()

        liked_movies: list[str] = []
        disliked_movies: list[str] = []
        watched_movies: list[str] = []
        saved_movies: list[str] = []

        liked_genres_counter: Counter[str] = Counter()
        disliked_genres_counter: Counter[str] = Counter()

        for item in preference_items:
            if item.preference == "like":
                liked_movies.append(item.title)
                self._update_genre_counter(liked_genres_counter, item.genres)
            elif item.preference == "dislike":
                disliked_movies.append(item.title)
                self._update_genre_counter(disliked_genres_counter, item.genres)

            if item.watched:
                watched_movies.append(item.title)
            if item.saved:
                saved_movies.append(item.title)

        return UserMemorySummary(
            user_id=user_id,
            total_feedback=len(preference_items),
            liked_movies=liked_movies[:10],
            disliked_movies=disliked_movies[:10],
            watched_movies=watched_movies[:10],
            saved_movies=saved_movies[:10],
            liked_genres=dict(liked_genres_counter.most_common(10)),
            disliked_genres=dict(disliked_genres_counter.most_common(10))
        )


    def _get_existing_preference(
        self,
        db: Session,
        user_id: str,
        movie_id: str,
    ) -> UserMoviePreference | None:
        """Check if there's an existing preference for the user/movie pair."""
        statement = (
            select(UserMoviePreference)
            .where(
                UserMoviePreference.user_id == user_id,
                UserMoviePreference.movie_id == movie_id,
            )
        )

        return db.execute(statement).scalar_one_or_none()


    def _update_genre_counter(self, counter: Counter[str], genres: str | None) -> None:
        """
        Update genre counts from a comma-separated genre string.

        Example:
            "Drama, Science Fiction" -> Drama += 1, Science Fiction += 1
        """
        if not genres:
            return
    
        for genre in genres.split(","):
            genre = genre.strip()
            if genre:
                counter[genre] += 1
        

    def _to_preference_response(self, preference: UserMoviePreference) -> UserMoviePreferenceResponse:
        """
        Convert a UserMoviePreference ORM object to a UserMoviePreferenceResponse Pydantic model.
        """
        return UserMoviePreferenceResponse(
            id=preference.id,
            user_id=preference.user_id,
            movie_id=preference.movie_id,
            title=preference.title,
            
            query=preference.query,
            genres=preference.genres,
            score=preference.score,

            preference=preference.preference,
            watched=preference.watched,
            saved=preference.saved,
            created_at=preference.created_at,
            updated_at=preference.updated_at,
        )
    
    def get_reranking_memory(
            self,
            db: Session,
            user_id: str,
    ) -> dict:
        """
        Return user memory in a format useful for reranking.

        This is based on current preference states, not raw click events.
        Since there is only one row per user/movie pair, repeated clicks
        do not inflate these signals.
        """
        statement = (
            select(UserMoviePreference)
            .where(UserMoviePreference.user_id == user_id)
        )
        
        preference_items = db.execute(statement).scalars().all()

        liked_genres: Counter[str] = Counter()
        disliked_genres: Counter[str] = Counter()
        watched_movie_ids: set[str] = set()
        saved_movie_ids: set[str] = set()
        liked_movie_ids: set[str] = set()
        disliked_movie_ids: set[str] = set()

        for item in preference_items:
            if item.preference == "like":
                liked_movie_ids.add(item.movie_id)
                self._update_genre_counter(liked_genres, item.genres)
            elif item.preference == "dislike":
                disliked_movie_ids.add(item.movie_id)
                self._update_genre_counter(disliked_genres, item.genres)

            if item.watched:
                watched_movie_ids.add(item.movie_id)
            if item.saved:
                saved_movie_ids.add(item.movie_id)
        
        return {
            "liked_genres": dict(liked_genres),
            "disliked_genres": dict(disliked_genres),
            "watched_movie_ids": list(watched_movie_ids),
            "saved_movie_ids": list(saved_movie_ids),
            "liked_movie_ids": list(liked_movie_ids),
            "disliked_movie_ids": list(disliked_movie_ids),
        }

        