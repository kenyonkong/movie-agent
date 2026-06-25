from typing import Any, Literal

from pydantic import BaseModel, Field

class HardConstraints(BaseModel):
    """
    Constraints that can be checked against explicit structured metadata.

    Only put truly hard requirements here.

    Example:
        "Only Korean-language movies"
        → allowed_languages=["ko"]

    Do not put vague preferences here.

    Example:
        "Something emotionally powerful"
        → not a hard metadata constraint
    """

    allowed_directors: list[str] | None = Field(default_factory=list)
    required_cast: list[str] | None = Field(default_factory=list)
    required_genres: list[str] | None = Field(default_factory=list)
    excluded_genres: list[str] | None = Field(default_factory=list)
    allowed_languages: list[str] | None = Field(default_factory=list)

    min_runtime: int | None = None
    max_runtime: int | None = None

    min_release_year: int | None = None
    max_release_year: int | None = None

    min_vote_average: float | None = None
    min_vote_count: int | None = None


class EvaluationQuery(BaseModel):
    """
    One manually designed recommendation evaluation query.
    """

    id: str
    query: str

    # Use a dedicated evaluation user rather than demo_user so
    # random development feedback does not change your measurements.
    user_id: str = "eval_neutral"

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    relevant_movie_ids: list[str] = Field(
        default_factory=list
    )

    relevant_titles: list[str] = Field(
        default_factory=list
    )

    hard_constraints: HardConstraints = Field(
        default_factory=HardConstraints
    )

    notes: str = ""


class EvaluationConfig(BaseModel):
    """
    One system configuration used in the ablation study.
    """
    name: str
    enabled: bool = True

    mode: Literal[
        "raw_retrieval", 
        "intent_retrieval",
        "agent",
    ]

    embedding_provider: Literal[
        "local", 
        "openai",
    ]

    embedding_model: str
    embedding_dimensions: int | None = None

    intent_provider: Literal[
        "template", 
        "openai",
    ] = "template"

    intent_model: str | None = None
    use_llm_intent: bool = False

    llm_reranker_provider: Literal[
        "disabled", 
        "openai",
    ] = "disabled"

    llm_reranker_model: str | None = None
    use_llm_reranker: bool = False

    # Repeating non-LLM retrieval calls makes latency measurements
    # less noisy. Keep LLM configurations at one or two repeats.
    latency_repeats: int = Field(
        default=1,
        ge=1,
        le=10,
    )

    notes: str = ""


class EvaluationMovie(BaseModel):
    movie_id: str
    title: str
    rank: int

    release_year: int | None = None

    genres: list[str] = Field(
        default_factory=list
    )

    director: str = ""

    cast: list[str] = Field(
        default_factory=list
    )

    runtime: int | None = None
    original_language: str = ""

    popularity: float = 0.0
    vote_average: float = 0.0
    vote_count: int = 0

    semantic_score: float | None = None
    final_score: float | None = None

    heuristic_rank: int | None = None
    llm_rank: int | None = None

    # Relative to the catalog's popularity distribution.
    catalog_novelty: float = 0.0


class EvaluationRun(BaseModel):
    """
    Raw output for one query under one configuration.
    """

    config_name: str
    query_id: str
    query: str

    retrieval_query: str

    embedding_identifier: str
    intent_provider: str | None = None
    reranker_provider: str | None = None

    latency_ms: float

    input_tokens: int = 0
    output_tokens: int = 0

    fallback_used: bool = False

    results: list[EvaluationMovie] = Field(
        default_factory=list
    )

    trace: dict[str, Any] | None = None
    error: str | None = None


