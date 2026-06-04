from pydantic import BaseModel, Field

from datetime import datetime
from typing import Literal

FeedbackAction = Literal["like", "dislike", "watched", "save"]
PreferenceValue = Literal["like", "dislike"]

class RecommendRequest(BaseModel):
    user_id: str = Field(
        default="demo_user",
        description="User ID used for personalization. For now, this can be demo_user.",
    )
    query: str = Field(
        ..., # Required field
        min_length=2,
        max_length=500,
        description="Natural-language movie preference query.",
    )
    top_k: int = Field(
        default=5, 
        ge=1,
        le=10,
        description="Number of movie recommendations to return.",
    )


class MovieRecommendation(BaseModel):
    movie_id: str
    title: str
    release_year: int | None = None
    genres: str | None = None

    # final score used for ranking
    score: float 
    # raw distance from the vector database (lower is more similar)
    distance: float
    # Score converted from vector distance. Higher means more similar.
    semantic_score: float
    # User-memory contribution from liked/disliked movies (positive means more similar, negative means less similar)
    preference_score: float

    # Current perference state. "like", "dislike", or None if no feedback given yet.
    preference: PreferenceValue | None = None

    # whether the movie was already watched
    watched: bool = False
    # whether the movie was already saved
    saved: bool = False

    reason: str
    document_preview: str
    # Debug information showing why this item received its final score.
    ranking_signals: dict[str, float | bool | str]


class RecommendResponse(BaseModel):
    user_id: str
    query: str
    top_k: int
    results: list[MovieRecommendation]
    latency_ms: float


class FeedbackRequest(BaseModel):
    user_id: str = Field(default="demo_user", min_length=1, max_length=128)
    movie_id: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=512)
    action: FeedbackAction

    query: str | None = Field(default=None, max_length=500)
    genres: str | None = None
    score: float | None = None


class UserMoviePreferenceResponse(BaseModel):
    id: int
    user_id: str
    movie_id: str
    title: str

    query: str | None = None
    genres: str | None = None
    score: float | None = None

    preference: PreferenceValue | None = None
    watched: bool
    saved: bool

    created_at: datetime
    updated_at: datetime


class UserMemorySummary(BaseModel):
    user_id: str
    total_feedback: int
    liked_movies: list[str]
    disliked_movies: list[str]
    watched_movies: list[str]
    saved_movies: list[str]
    liked_genres: dict[str, int] # Genre name -> count
    disliked_genres: dict[str, int] # Genre name -> count