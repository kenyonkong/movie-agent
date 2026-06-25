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


class MovieHardConstraints(BaseModel):
    """
    Exact constraints that every returned movie must satisfy.

    List semantics:

    allowed_directors:
        The movie may match any one listed director.

    required_cast:
        Every listed cast member must appear.

    required_genres:
        Every listed genre must appear.

    excluded_genres:
        None of the listed genres may appear.

    allowed_languages:
        The movie may use any one listed language code.
    """

    allowed_directors: list[str] = Field(default_factory=list)
    required_cast: list[str] = Field(default_factory=list)

    required_genres: list[str] = Field(default_factory=list)
    excluded_genres: list[str] = Field(default_factory=list)

    allowed_languages: list[str] = Field(default_factory=list)

    min_runtime: int | None = Field(
        default=None,
        ge=1,
    )
    max_runtime: int | None = Field(
        default=None,
        ge=1,
    )

    min_release_year: int | None = Field(
        default=None,
        ge=1870,
    )
    max_release_year: int | None = Field(
        default=None,
        ge=1870,
    )

    min_vote_average: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
    )

    min_vote_count: int | None = Field(
        default=None,
        ge=0,
    )

    def is_empty(self) -> bool:
        """
        Return True when no hard constraint is active.
        """
        return not any(
            [
                self.allowed_directors,
                self.required_cast,
                self.required_genres,
                self.excluded_genres,
                self.allowed_languages,
                self.min_runtime is not None,
                self.max_runtime is not None,
                self.min_release_year is not None,
                self.max_release_year is not None,
                self.min_vote_average is not None,
                self.min_vote_count is not None,
            ]
        )
    
# Only used for reporting hard constraints for debugging purposes
class ConstraintReport(BaseModel):
    """
    Observable report describing hard-constraint enforcement.
    """

    enabled: bool
    active: bool

    descriptions: list[str] = Field(default_factory=list)

    # Useful for debug mode. This is not a secret.
    chroma_where: dict[str, Any] | None = None

    retrieved_candidate_count: int = 0
    valid_candidate_count: int = 0
    post_filter_rejected_count: int = 0

    requested_top_k: int = 0
    result_shortfall: int = 0

    violation_counts: dict[str, int] = Field(
        default_factory=dict
    )    
    

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

    # Human-readable constraints retained for UI/debugging purposes
    constraints: list[str] = Field(default_factory=list)

    # Hard constraints that used for filtering movies
    hard_constraints: MovieHardConstraints = Field(default_factory=MovieHardConstraints)

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
    use_llm_intent: bool = Field(
        default=False,
        description=(
            "Whether to parse the raw query into structured movie intent using "
            "the configured intent parser provider."
        ),
    )
    enforce_hard_constraints: bool = Field(
        default=True,
        description=(
            "Whether structured hard constraints should be applied. "
            "When enabled, invalid movies are never added merely to fill top_k."
        ),
    )
    use_llm_reranker: bool = Field(
        default=False,
        description=(
            "Whether the MovieAgent should use the configured bounded "
            "LLM reranker over the heuristic candidate shortlist."
        ),
    )
    use_llm_explanations: bool = Field(
        default=False,
        description=(
            "Whether to generate explanations using the configured LLM provider. "
            "If false, template explanations are used."
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

    # TMDB image data
    poster_path: str | None = None
    poster_url: str | None = None
    backdrop_path: str | None = None
    backdrop_url: str | None = None

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

    # Rank using openAI
    heuristic_rank: int | None = None
    llm_rank: int | None = None
    llm_rerank_reason: str | None = None

    reason: str
    document_preview: str
    # Debug information showing why this item received its final score.
    ranking_signals: dict[str, float | bool | str | int]


class RecommendResponse(BaseModel):
    user_id: str
    query: str
    retrieval_query: str
    parsed_intent: MovieIntent
    intent_provider: str

    constraint_report: ConstraintReport 

    top_k: int
    include_watched: bool
    candidate_count: int
    filtered_watched_count: int
    explanation_provider: str

    reranker_provider: str
    reranker_fallback_used: bool

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

