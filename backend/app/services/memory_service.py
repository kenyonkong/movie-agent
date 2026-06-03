from collections import Counter

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import UserFeedback
from app.db.schemas import (FeedbackRequest, FeedbackResponse, UserMemorySummary,)


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
    ) -> FeedbackResponse:
        """
        Save one user feedback to the database.

        Args:
            db: Database session
            request: FeedbackRequest containing user feedback details

        Returns:
            FeedbackResponse with saved feedback details
        """
        feedback = UserFeedback(
            user_id=request.user_id,
            movie_id=request.movie_id,
            title=request.title,
            action=request.action,
            query=request.query,
            genres=request.genres,
            score=request.score,
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return self._to_feedback_response(feedback)
    

    def get_recent_feedback(
        self,
        db: Session,
        user_id: str,
        limit: int = 10,
    ) -> list[FeedbackResponse]:
        """
        Return recent feedback events for one user.
        """
        statement = (
            select(UserFeedback)
            .where(UserFeedback.user_id == user_id)
            .order_by(desc(UserFeedback.created_at))
            .limit(limit)
        )
        
        feedbacks = db.execute(statement).scalars().all()
        return [self._to_feedback_response(feedback) for feedback in feedbacks]
    

    def get_memory_summary(
        self,
        db: Session,
        user_id: str,
    ) -> UserMemorySummary:
        """
        Return a summary of the user's feedback history, including liked/disliked movies and genres.
        """
        statement = (
            select(UserFeedback)
            .where(UserFeedback.user_id == user_id)
            .order_by(desc(UserFeedback.created_at))
        )
        
        feedback_items = db.execute(statement).scalars().all()

        liked_movies: list[str] = []
        disliked_movies: list[str] = []
        watched_movies: list[str] = []
        saved_movies: list[str] = []

        liked_genres_counter: Counter[str] = Counter()
        disliked_genres_counter: Counter[str] = Counter()

        for item in feedback_items:
            if item.action == "like":
                liked_movies.append(item.title)
                self._update_genre_counter(liked_genres_counter, item.genres)
            elif item.action == "dislike":
                disliked_movies.append(item.title)
                self._update_genre_counter(disliked_genres_counter, item.genres)
            elif item.action == "watched":
                watched_movies.append(item.title)
            elif item.action == "save":
                saved_movies.append(item.title)

        return UserMemorySummary(
            user_id=user_id,
            total_feedback=len(feedback_items),
            liked_movies=liked_movies[:10],
            disliked_movies=disliked_movies[:10],
            watched_movies=watched_movies[:10],
            saved_movies=saved_movies[:10],
            liked_genres=dict(liked_genres_counter.most_common(10)),
            disliked_genres=dict(disliked_genres_counter.most_common(10))
        )

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
        
    def _to_feedback_response(self, feedback: UserFeedback) -> FeedbackResponse:
        """
        Convert a UserFeedback ORM object to a FeedbackResponse Pydantic model.
        """
        return FeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            movie_id=feedback.movie_id,
            title=feedback.title,
            action=feedback.action,
            query=feedback.query,
            genres=feedback.genres,
            score=feedback.score,
            created_at=feedback.created_at,
        )