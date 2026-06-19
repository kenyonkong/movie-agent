from typing import Any

from app.db.schemas import MovieRecommendation

class RecommendationFormatter:
    """
    Converts internal candidate dictionaries into public API schemas.

    The agent and reranker can use flexible dictionaries internally.
    The API response remains strongly validated by Pydantic.
    """
    def prepare_document_previews(
        self,
        candidates: list[dict[str, Any]],
        max_chars: int = 500,
    ) -> None:
        """
        Mutates candidates by adding a shortened document_preview field.
        """
        for candidate in candidates:
            document = str(candidate.get("document") or "").strip()

            if len(document) <= max_chars:
                preview = document
            else:
                preview = document[:max_chars].rstrip() + "..."

            candidate["document_preview"] = preview

    
    def format_many(
        self,
        candidates: list[dict[str, Any]],
        explanations: list[str],
    ) -> list[MovieRecommendation]:
        if len(candidates) != len(explanations):
            raise ValueError(
                "Candidate and explanation counts do not match: "
                f"{len(candidates)} candidates, "
                f"{len(explanations)} explanations."
            )

        return [
            self.format_one(candidate, explanation)
            for candidate, explanation in zip(
                candidates,
                explanations,
            )
        ]
    
    
    def format_one(
        self,
        candidate: dict[str, Any],
        explanation: str,
    ) -> MovieRecommendation:
        release_year = self._safe_int(
            candidate.get("release_year")
        )

        if release_year == -1:
            release_year = None

        preference_value = candidate.get("preference")

        preference = (
            preference_value
            if preference_value in {"like", "dislike"}
            else None
        )

        return MovieRecommendation(
            movie_id=str(candidate.get("id")),
            title=str(
                candidate.get("title") or "Unknown Title"
            ),
            release_year=release_year,
            genres=self._optional_string(
                candidate.get("genres")
            ),
            score=round(
                float(candidate.get("final_score", 0.0)),
                4,
            ),
            distance=round(
                float(candidate.get("distance", 0.0)),
                4,
            ),
            semantic_score=round(
                float(candidate.get("semantic_score", 0.0)),
                4,
            ),
            preference_score=round(
                float(candidate.get("preference_score", 0.0)),
                4,
            ),
            novelty_score=round(
                float(candidate.get("novelty_score", 0.0)),
                4,
            ),
            diversity_penalty=round(
                float(candidate.get("diversity_penalty", 0.0)),
                4,
            ),
            preference=preference,
            watched=bool(candidate.get("watched", False)),
            saved=bool(candidate.get("saved", False)),
            popularity=self._safe_float(
                candidate.get("popularity")
            ),
            vote_average=self._safe_float(
                candidate.get("vote_average")
            ),
            vote_count=self._safe_int(
                candidate.get("vote_count")
            ),
            reason=explanation,
            document_preview=str(
                candidate.get("document_preview") or ""
            ),
            ranking_signals=candidate.get(
                "ranking_signals",
                {},
            ),
        )
    

    def _safe_float(self, value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    

    def _safe_int(self, value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None
        

    def _optional_string(self, value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text or None