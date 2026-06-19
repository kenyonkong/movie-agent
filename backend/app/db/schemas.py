from pydantic import BaseModel, Field

from datetime import datetime
from typing import Literal, Any

FeedbackAction = Literal["like", "dislike", "watched", "save"]
PreferenceValue = Literal["like", "dislike"]

class AgentTraceStep(BaseModel):
    """
    One observable step in the MovieAgent workflow.

    The trace should contain operational information, not secrets,
    full prompts, API keys, or the user's complete stored memory.
    """

    name: str
    status: Literal["completed", "skipped", "failed"]
    duration_ms: float
    details: dict[str, Any] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    """
    Sanitized execution trace returned for debugging and learning.
    """

    agent_name: str = "movie_agent"
    agent_version: str = "day15"
    total_duration_ms: float
    steps: list[AgentTraceStep] = Field(default_factory=list)


class MovieIntent(BaseModel):
    """
    Structured interpretation of the user's natural-language movie request.

    This is produced by the intent parser and used to improve retrieval.
    """

    raw_query: str
    query_rewrite: str

    reference_movies: list[str] = Field(default_factory=list)
    moods: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)

    pacing: str | None = None
    tone: list[str] = Field(default_factory=list)

    avoid: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    parser_notes: str = ""


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
    include_watched: bool = Field(
        default=False,
        description="Whether to include movies the user has already watched in the recommendations.",
    )
    use_llm_explanations: bool = Field(
        default=False,
        description=(
            "Whether to generate explanations using the configured LLM provider. "
            "If false, template explanations are used."
        ),
    )
    use_llm_intent: bool = Field(
        default=False,
        description=(
            "Whether to parse the raw query into structured movie intent using "
            "the configured intent parser provider."
        ),
    )
    include_agent_trace: bool = Field(
        default=False,
        description=(
            "Whether the response should include a sanitized MovieAgent "
            "execution trace."
        ),
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

    # small boost for novelty
    novelty_score: float

    diversity_penalty: float

    # Current perference state. "like", "dislike", or None if no feedback given yet.
    preference: PreferenceValue | None = None

    # whether the movie was already watched
    watched: bool = False
    # whether the movie was already saved
    saved: bool = False

    popularity: float | None = None
    vote_average: float | None = None
    vote_count: int | None = None

    reason: str
    document_preview: str
    # Debug information showing why this item received its final score.
    ranking_signals: dict[str, float | bool | str]


class RecommendResponse(BaseModel):
    user_id: str
    query: str
    retrieval_query: str
    parsed_intent: MovieIntent
    intent_provider: str

    top_k: int
    include_watched: bool
    candidate_count: int
    filtered_watched_count: int
    explanation_provider: str

    results: list[MovieRecommendation]
    latency_ms: float
    agent_trace: AgentTrace | None = None


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