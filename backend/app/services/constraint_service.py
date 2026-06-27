from dataclasses import dataclass
from typing import Any

from app.db.schemas import (
    ConstraintReport,
    MovieHardConstraints,
)
from app.services.vector_store import (
    normalize_filter_text,
    split_metadata_values,
)


@dataclass(frozen=True)
class ConstraintPlan:
    """
    Executable plan generated from structured hard constraints.
    """

    constraints: MovieHardConstraints

    active: bool

    chroma_where: dict[str, Any] | None

    descriptions: list[str]


@dataclass
class ConstraintFilterResult:
    """
    Result of deterministic candidate validation.
    """

    candidates: list[dict[str, Any]]

    rejected_count: int

    violation_counts: dict[str, int]


class MovieConstraintService:
    """
    Converts structured hard constraints into:

    1. Chroma metadata filters for efficient retrieval.
    2. Deterministic Python validation for correctness.

    The Python validator is the final authority.
    """

    def passthrough_result(
        self,
        candidates: list[dict[str, Any]],
    ) -> ConstraintFilterResult:
        return ConstraintFilterResult(
            candidates=candidates,
            rejected_count=0,
            violation_counts={},
        )
    
    
    def build_plan(
        self,
        constraints: MovieHardConstraints,
    ) -> ConstraintPlan:
        if constraints.is_empty():
            return ConstraintPlan(
                constraints=constraints,
                active=False,
                chroma_where=None,
                descriptions=[],
            )

        conditions: list[
            dict[str, Any]
        ] = []

        descriptions: list[str] = []

        if constraints.allowed_directors:
            director_conditions = [
                {
                    "directors_normalized": {
                        "$contains": (
                            normalize_filter_text(
                                director
                            )
                        )
                    }
                }
                for director
                in constraints.allowed_directors
            ]

            if len(director_conditions) == 1:
                conditions.append(
                    director_conditions[0]
                )
            else:
                conditions.append(
                    {
                        "$or": (
                            director_conditions
                        )
                    }
                )

            descriptions.append(
                "Director is one of: "
                + ", ".join(
                    constraints.allowed_directors
                )
            )

        for cast_member in (
            constraints.required_cast
        ):
            conditions.append(
                {
                    "cast_normalized": {
                        "$contains": (
                            normalize_filter_text(
                                cast_member
                            )
                        )
                    }
                }
            )

            descriptions.append(
                f"Cast includes {cast_member}"
            )

        for genre in (
            constraints.required_genres
        ):
            conditions.append(
                {
                    "genres_normalized": {
                        "$contains": (
                            normalize_filter_text(
                                genre
                            )
                        )
                    }
                }
            )

            descriptions.append(
                f"Genre includes {genre}"
            )

        for genre in (
            constraints.excluded_genres
        ):
            conditions.append(
                {
                    "genres_normalized": {
                        "$not_contains": (
                            normalize_filter_text(
                                genre
                            )
                        )
                    }
                }
            )

            descriptions.append(
                f"Genre excludes {genre}"
            )

        if constraints.allowed_languages:
            language_codes = [
                language.strip().lower()
                for language
                in constraints.allowed_languages
                if language.strip()
            ]

            conditions.append(
                {
                    "original_language": {
                        "$in": language_codes
                    }
                }
            )

            descriptions.append(
                "Original language is one of: "
                + ", ".join(
                    language_codes
                )
            )

        if constraints.min_runtime is not None:
            conditions.append(
                {
                    "runtime": {
                        "$gte": (
                            constraints.min_runtime
                        )
                    }
                }
            )

            descriptions.append(
                "Runtime is at least "
                f"{constraints.min_runtime} minutes"
            )

        if constraints.max_runtime is not None:
            conditions.append(
                {
                    "runtime": {
                        "$lte": (
                            constraints.max_runtime
                        )
                    }
                }
            )

            descriptions.append(
                "Runtime is at most "
                f"{constraints.max_runtime} minutes"
            )

        if (
            constraints.min_release_year
            is not None
        ):
            conditions.append(
                {
                    "release_year": {
                        "$gte": (
                            constraints
                            .min_release_year
                        )
                    }
                }
            )

            descriptions.append(
                "Release year is at least "
                f"{constraints.min_release_year}"
            )

        if (
            constraints.max_release_year
            is not None
        ):
            conditions.append(
                {
                    "release_year": {
                        "$lte": (
                            constraints
                            .max_release_year
                        )
                    }
                }
            )

            descriptions.append(
                "Release year is at most "
                f"{constraints.max_release_year}"
            )

        if (
            constraints.min_vote_average
            is not None
        ):
            conditions.append(
                {
                    "vote_average": {
                        "$gte": (
                            constraints
                            .min_vote_average
                        )
                    }
                }
            )

            descriptions.append(
                "Rating is at least "
                f"{constraints.min_vote_average}"
            )

        if (
            constraints.min_vote_count
            is not None
        ):
            conditions.append(
                {
                    "vote_count": {
                        "$gte": (
                            constraints
                            .min_vote_count
                        )
                    }
                }
            )

            descriptions.append(
                "Vote count is at least "
                f"{constraints.min_vote_count}"
            )

        if not conditions:
            chroma_where = None
        elif len(conditions) == 1:
            chroma_where = conditions[0]
        else:
            chroma_where = {
                "$and": conditions
            }

        return ConstraintPlan(
            constraints=constraints,
            active=True,
            chroma_where=chroma_where,
            descriptions=descriptions,
        )


    def filter_candidates(
        self,
        candidates: list[dict[str, Any]],
        plan: ConstraintPlan,
    ) -> ConstraintFilterResult:
        """
        Revalidate every candidate deterministically.

        Even candidates returned by a filtered Chroma query are checked
        again. This protects against missing, malformed, or stale metadata.
        """
        if not plan.active:
            return ConstraintFilterResult(
                candidates=candidates,
                rejected_count=0,
                violation_counts={},
            )

        valid_candidates: list[
            dict[str, Any]
        ] = []

        violation_counts: dict[
            str,
            int,
        ] = {}

        for candidate in candidates:
            violations = (
                self._find_violations(
                    candidate=candidate,
                    constraints=(
                        plan.constraints
                    ),
                )
            )

            if not violations:
                valid_candidates.append(
                    candidate
                )
                continue

            for violation in violations:
                violation_counts[violation] = (
                    violation_counts.get(
                        violation,
                        0,
                    )
                    + 1
                )

        return ConstraintFilterResult(
            candidates=valid_candidates,
            rejected_count=(
                len(candidates)
                - len(valid_candidates)
            ),
            violation_counts=(
                violation_counts
            ),
        )

    def build_report(
        self,
        *,
        enabled: bool,
        plan: ConstraintPlan,
        retrieved_candidate_count: int,
        filter_result: ConstraintFilterResult,
        requested_top_k: int,
    ) -> ConstraintReport:
        valid_count = len(
            filter_result.candidates
        )

        return ConstraintReport(
            enabled=enabled,
            active=(
                enabled and plan.active
            ),
            descriptions=(
                plan.descriptions
                if enabled
                else []
            ),
            chroma_where=(
                plan.chroma_where
                if enabled
                else None
            ),
            retrieved_candidate_count=(
                retrieved_candidate_count
            ),
            valid_candidate_count=(
                valid_count
            ),
            post_filter_rejected_count=(
                filter_result.rejected_count
            ),
            requested_top_k=(
                requested_top_k
            ),
            result_shortfall=max(
                requested_top_k
                - valid_count,
                0,
            ),
            violation_counts=(
                filter_result.violation_counts
            ),
        )

    def _find_violations(
        self,
        *,
        candidate: dict[str, Any],
        constraints: MovieHardConstraints,
    ) -> list[str]:
        violations: list[str] = []

        directors = self._normalized_values(
            candidate,
            normalized_key=(
                "directors_normalized"
            ),
            display_key="director",
        )

        if constraints.allowed_directors:
            allowed_directors = {
                normalize_filter_text(
                    director
                )
                for director
                in constraints.allowed_directors
            }

            if not (
                directors
                & allowed_directors
            ):
                violations.append(
                    "director"
                )

        cast_members = self._normalized_values(
            candidate,
            normalized_key=(
                "cast_normalized"
            ),
            display_key="cast",
        )

        for required_cast_member in (
            constraints.required_cast
        ):
            if (
                normalize_filter_text(
                    required_cast_member
                )
                not in cast_members
            ):
                violations.append(
                    "cast"
                )
                break

        genres = self._normalized_values(
            candidate,
            normalized_key=(
                "genres_normalized"
            ),
            display_key="genres",
        )

        for required_genre in (
            constraints.required_genres
        ):
            if (
                normalize_filter_text(
                    required_genre
                )
                not in genres
            ):
                violations.append(
                    "required_genre"
                )
                break

        for excluded_genre in (
            constraints.excluded_genres
        ):
            if (
                normalize_filter_text(
                    excluded_genre
                )
                in genres
            ):
                violations.append(
                    "excluded_genre"
                )
                break

        if constraints.allowed_languages:
            allowed_languages = {
                language.strip().lower()
                for language
                in constraints.allowed_languages
            }

            candidate_language = str(
                candidate.get(
                    "original_language"
                )
                or ""
            ).strip().lower()

            if (
                not candidate_language
                or candidate_language
                not in allowed_languages
            ):
                violations.append(
                    "original_language"
                )

        runtime = self._optional_int(
            candidate.get("runtime")
        )

        if constraints.min_runtime is not None:
            if (
                runtime is None
                or runtime
                < constraints.min_runtime
            ):
                violations.append(
                    "min_runtime"
                )

        if constraints.max_runtime is not None:
            if (
                runtime is None
                or runtime
                > constraints.max_runtime
            ):
                violations.append(
                    "max_runtime"
                )

        release_year = self._optional_int(
            candidate.get(
                "release_year"
            )
        )

        if (
            constraints.min_release_year
            is not None
        ):
            if (
                release_year is None
                or release_year
                < constraints.min_release_year
            ):
                violations.append(
                    "min_release_year"
                )

        if (
            constraints.max_release_year
            is not None
        ):
            if (
                release_year is None
                or release_year
                > constraints.max_release_year
            ):
                violations.append(
                    "max_release_year"
                )

        vote_average = self._optional_float(
            candidate.get(
                "vote_average"
            )
        )

        if (
            constraints.min_vote_average
            is not None
        ):
            if (
                vote_average is None
                or vote_average
                < constraints.min_vote_average
            ):
                violations.append(
                    "min_vote_average"
                )

        vote_count = self._optional_int(
            candidate.get(
                "vote_count"
            )
        )

        if constraints.min_vote_count is not None:
            if (
                vote_count is None
                or vote_count
                < constraints.min_vote_count
            ):
                violations.append(
                    "min_vote_count"
                )

        return violations

    def _normalized_values(
        self,
        candidate: dict[str, Any],
        normalized_key: str,
        display_key: str,
    ) -> set[str]:
        existing = candidate.get(
            normalized_key
        )

        if isinstance(existing, list):
            return {
                normalize_filter_text(value)
                for value in existing
                if normalize_filter_text(
                    value
                )
            }

        return set(
            split_metadata_values(
                candidate.get(display_key)
            )
        )

    def _optional_int(
        self,
        value: Any,
    ) -> int | None:
        if value in {
            None,
            "",
        }:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def _optional_float(
        self,
        value: Any,
    ) -> float | None:
        if value in {
            None,
            "",
        }:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None