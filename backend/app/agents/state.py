from dataclasses import dataclass, field
from typing import Any

from app.db.schemas import MovieIntent, RecommendRequest

@dataclass
class MovieAgentState:
    """
    Mutable state for one MovieAgent recommendation run.

    Each request receives a fresh state object.
    Never share this object between users or requests.
    """

    request: RecommendRequest

    parsed_intent: MovieIntent | None = None
    retrieval_query: str = ""

    user_memory: dict[str, Any] = field(default_factory=dict)
    raw_candidates: list[dict[str, Any]] = field(default_factory=list)
    filtered_candidates: list[dict[str, Any]] = field(default_factory=list)
    candidates_for_reranking: list[dict[str, Any]] = field(default_factory=list)

    heuristic_candidates: list[dict[str, Any]] = field(default_factory=list)

    # Day 16 will populate this with the bounded LLM reranker.
    final_candidates: list[dict[str, Any]] = field(default_factory=list)

    explanations: list[str] = field(default_factory=list)

    filtered_watched_count: int = 0
    watched_filter_fallback_used: bool = False