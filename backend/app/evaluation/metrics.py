import math
import statistics
from typing import Any

from app.evaluation.models import (
    EvaluationMovie,
    EvaluationQuery,
    EvaluationRun,
    HardConstraints,
)


def normalize_text(value: Any) -> str:
    return " ".join(
        str(value or "").casefold().split()
    )


def safe_mean(
    values: list[float | int | None],
) -> float | None:
    cleaned = [
        float(value)
        for value in values
        if value is not None
    ]

    if not cleaned:
        return None

    return round(
        statistics.mean(cleaned),
        4,
    )


# Calculate the percentile of a list of values.
def percentile(
    values: list[float],
    percentile_value: float,
) -> float | None:
    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return round(ordered[0], 4)

    position = (
        len(ordered) - 1
    ) * percentile_value

    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return round(
            ordered[lower_index],
            4,
        )

    weight = position - lower_index

    result = (
        ordered[lower_index] * (1 - weight)
        + ordered[upper_index] * weight
    )

    return round(result, 4)


def movie_is_relevant(
    movie: EvaluationMovie,
    query: EvaluationQuery,
) -> bool:
    relevant_ids = {
        str(movie_id)
        for movie_id in query.relevant_movie_ids
    }

    relevant_titles = {
        normalize_text(title)
        for title in query.relevant_titles
    }

    return (
        movie.movie_id in relevant_ids
        or normalize_text(movie.title)
        in relevant_titles
    )

# Check if at least one relevant movie is in the top-k results, 0 or 1
def hit_at_k(
    movies: list[EvaluationMovie],
    query: EvaluationQuery,
) -> float | None:
    if (
        not query.relevant_movie_ids
        and not query.relevant_titles
    ):
        return None

    return float(
        any(
            movie_is_relevant(movie, query)
            for movie in movies
        )
    )

# calculate the percentage of relevant movies in the top-k results
def precision_at_k(
    movies: list[EvaluationMovie],
    query: EvaluationQuery,
) -> float | None:
    if not movies:
        return 0.0

    if (
        not query.relevant_movie_ids
        and not query.relevant_titles
    ):
        return None

    relevant_count = sum(
        movie_is_relevant(movie, query)
        for movie in movies
    )

    return round(
        relevant_count / len(movies),
        4,
    )

# number of relevant movies retrieved / total number of relevant movies
def recall_at_k(
    movies: list[EvaluationMovie],
    query: EvaluationQuery,
) -> float | None:
    total_labeled = len(
        set(query.relevant_movie_ids)
    ) + len(
        {
            normalize_text(title)
            for title in query.relevant_titles
        }
    )

    if total_labeled == 0:
        return None

    matched_ids: set[str] = set()
    matched_titles: set[str] = set()

    relevant_ids = {
        str(movie_id)
        for movie_id in query.relevant_movie_ids
    }

    relevant_titles = {
        normalize_text(title)
        for title in query.relevant_titles
    }

    for movie in movies:
        if movie.movie_id in relevant_ids:
            matched_ids.add(movie.movie_id)

        normalized_title = normalize_text(
            movie.title
        )

        if normalized_title in relevant_titles:
            matched_titles.add(normalized_title)

    matched_count = (
        len(matched_ids)
        + len(matched_titles)
    )

    return round(
        matched_count / total_labeled,
        4,
    )


# How early does the first relevant movie appear
def reciprocal_rank(
    movies: list[EvaluationMovie],
    query: EvaluationQuery,
) -> float | None:
    if (
        not query.relevant_movie_ids
        and not query.relevant_titles
    ):
        return None

    for movie in movies:
        if movie_is_relevant(movie, query):
            return round(
                1.0 / movie.rank,
                4,
            )

    return 0.0


# calculate the discounted cumulative gain
def dcg(grades: list[int]) -> float:
    total = 0.0

    for index, grade in enumerate(
        grades,
        start=1,
    ):
        gain = (2**grade) - 1 # makes high grades more valuable
        discount = math.log2(index + 1) # reduces the impact of later items

        total += gain / discount

    return total

# nDCG rewards systems that place highly relevant movies near the top.
def ndcg_at_k(
    movies: list[EvaluationMovie],
    judgments: dict[str, int],
) -> float | None:
    if not judgments:
        return None

    grades = [
        int(
            judgments.get(
                movie.movie_id,
                0,
            )
        )
        for movie in movies
    ]

    actual_dcg = dcg(grades)

    ideal_grades = sorted(
        [
            int(grade)
            for grade in judgments.values()
        ],
        reverse=True,
    )[: len(movies)]

    ideal_dcg = dcg(ideal_grades)

    if ideal_dcg == 0:
        return 0.0

    return round(
        actual_dcg / ideal_dcg,
        4,
    )


def judgment_coverage(
    movies: list[EvaluationMovie],
    judgments: dict[str, int],
) -> float | None:
    if not movies:
        return 0.0

    if not judgments:
        return None

    judged_count = sum(
        movie.movie_id in judgments
        for movie in movies
    )

    return round(
        judged_count / len(movies),
        4,
    )


def genre_jaccard_distance(
    left: set[str],
    right: set[str],
) -> float:
    union = left | right

    if not union:
        return 0.0

    similarity = (
        len(left & right)
        / len(union)
    )

    return 1.0 - similarity


def intra_list_diversity(
    movies: list[EvaluationMovie],
) -> float | None:
    if len(movies) < 2:
        return None

    distances: list[float] = []

    for left_index in range(
        len(movies)
    ):
        for right_index in range(
            left_index + 1,
            len(movies),
        ):
            left_genres = {
                normalize_text(genre)
                for genre in movies[
                    left_index
                ].genres
            }

            right_genres = {
                normalize_text(genre)
                for genre in movies[
                    right_index
                ].genres
            }

            distances.append(
                genre_jaccard_distance(
                    left_genres,
                    right_genres,
                )
            )

    return safe_mean(distances)


def check_constraints(
    movie: EvaluationMovie,
    constraints: HardConstraints,
) -> list[bool]:
    """
    Return one boolean per checkable requirement.
    """
    checks: list[bool] = []

    normalized_director = normalize_text(
        movie.director
    )

    if constraints.allowed_directors:
        allowed_directors = {
            normalize_text(director)
            for director
            in constraints.allowed_directors
        }

        checks.append(
            normalized_director
            in allowed_directors
        )

    normalized_cast = {
        normalize_text(person)
        for person in movie.cast
    }

    for required_person in (
        constraints.required_cast
    ):
        required_name = normalize_text(
            required_person
        )

        checks.append(
            required_name in normalized_cast
            or any(
                required_name
                in cast_name
                for cast_name
                in normalized_cast
            )
        )

    normalized_genres = {
        normalize_text(genre)
        for genre in movie.genres
    }

    for genre in (
        constraints.required_genres
    ):
        checks.append(
            normalize_text(genre)
            in normalized_genres
        )

    for genre in (
        constraints.excluded_genres
    ):
        checks.append(
            normalize_text(genre)
            not in normalized_genres
        )

    if constraints.allowed_languages:
        checks.append(
            normalize_text(
                movie.original_language
            )
            in {
                normalize_text(language)
                for language
                in constraints.allowed_languages
            }
        )

    if constraints.min_runtime is not None:
        checks.append(
            movie.runtime is not None
            and movie.runtime
            >= constraints.min_runtime
        )

    if constraints.max_runtime is not None:
        checks.append(
            movie.runtime is not None
            and movie.runtime
            <= constraints.max_runtime
        )

    if (
        constraints.min_release_year
        is not None
    ):
        checks.append(
            movie.release_year is not None
            and movie.release_year
            >= constraints.min_release_year
        )

    if (
        constraints.max_release_year
        is not None
    ):
        checks.append(
            movie.release_year is not None
            and movie.release_year
            <= constraints.max_release_year
        )

    if (
        constraints.min_vote_average
        is not None
    ):
        checks.append(
            movie.vote_average
            >= constraints.min_vote_average
        )

    if constraints.min_vote_count is not None:
        checks.append(
            movie.vote_count
            >= constraints.min_vote_count
        )

    return checks


def constraint_metrics(
    movies: list[EvaluationMovie],
    constraints: HardConstraints,
) -> dict[str, float | None]:
    all_checks: list[bool] = [] # Stores every individual constraint result across every movie.
    full_matches: list[bool] = [] # how many movies satisfy every constraint

    for movie in movies:
        checks = check_constraints(
            movie,
            constraints,
        )

        if not checks:
            continue

        all_checks.extend(checks)
        full_matches.append(all(checks))

    if not all_checks:
        return {
            "constraint_check_accuracy": None,
            "fully_valid_result_rate": None,
            "top1_fully_valid": None,
        }

    top1_checks = (
        check_constraints(
            movies[0],
            constraints,
        )
        if movies
        else []
    )

    return {
        "constraint_check_accuracy": round(
            sum(all_checks)
            / len(all_checks),
            4,
        ),
        "fully_valid_result_rate": round(
            sum(full_matches)
            / len(full_matches),
            4,
        ),
        "top1_fully_valid": (
            float(all(top1_checks))
            if top1_checks
            else None
        ),
    }


def evaluate_run(
    run: EvaluationRun,
    query: EvaluationQuery,
    judgments: dict[str, int],
) -> dict[str, Any]:
    '''
    hit_at_k: whether at least one relevant movie appeared
    precision_at_k: what fraction of returned movies were relevant
    recall_at_k: what fraction of known relevant movies were retrieved
    reciprocal_rank: how early the first relevant movie appeared
    ndcg_at_k: whether highly relevant movies were ranked near the top
    judgment_coverage: how many returned movies had human relevance labels
    intra_list_diversity: how diverse the returned movies are
    average_catalog_novelty: how uncommon or less-popular the recommendations are
    '''
    constraint_values = constraint_metrics(
        run.results,
        query.hard_constraints,
    )

    return {
        "config_name": run.config_name,
        "query_id": query.id,
        "latency_ms": run.latency_ms,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "fallback_used": run.fallback_used,
        "error": run.error,
        "hit_at_k": hit_at_k(
            run.results,
            query,
        ),
        "precision_at_k": precision_at_k(
            run.results,
            query,
        ),
        "recall_at_k": recall_at_k(
            run.results,
            query,
        ),
        "reciprocal_rank": reciprocal_rank(
            run.results,
            query,
        ),
        "ndcg_at_k": ndcg_at_k(
            run.results,
            judgments,
        ),
        "judgment_coverage": judgment_coverage(
            run.results,
            judgments,
        ),
        "intra_list_diversity": (
            intra_list_diversity(
                run.results
            )
        ),
        "average_catalog_novelty": safe_mean(
            [
                movie.catalog_novelty
                for movie in run.results
            ]
        ),
        **constraint_values,
    }


def aggregate_config_metrics(
    metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for row in metric_rows:
        grouped.setdefault(
            row["config_name"],
            [],
        ).append(row)

    summaries: list[dict[str, Any]] = []

    metric_names = [
        "hit_at_k",
        "precision_at_k",
        "recall_at_k",
        "reciprocal_rank",
        "ndcg_at_k",
        "judgment_coverage",
        "intra_list_diversity",
        "average_catalog_novelty",
        "constraint_check_accuracy",
        "fully_valid_result_rate",
        "top1_fully_valid",
    ]

    for config_name, rows in grouped.items():
        latencies = [
            float(row["latency_ms"])
            for row in rows
            if row.get("error") is None
        ]

        summary: dict[str, Any] = {
            "config_name": config_name,
            "query_count": len(rows),
            "error_count": sum(
                row.get("error") is not None
                for row in rows
            ),
            "fallback_rate": round(
                sum(
                    bool(
                        row.get(
                            "fallback_used"
                        )
                    )
                    for row in rows
                )
                / len(rows),
                4,
            )
            if rows
            else 0.0,
            "total_input_tokens": sum(
                int(
                    row.get(
                        "input_tokens",
                        0,
                    )
                    or 0
                )
                for row in rows
            ),
            "total_output_tokens": sum(
                int(
                    row.get(
                        "output_tokens",
                        0,
                    )
                    or 0
                )
                for row in rows
            ),
            "latency_p50_ms": percentile(
                latencies,
                0.50,
            ),
            "latency_p95_ms": percentile(
                latencies,
                0.95,
            ),
        }

        for metric_name in metric_names:
            summary[metric_name] = safe_mean(
                [
                    row.get(metric_name)
                    for row in rows
                ]
            )

        summaries.append(summary)

    return summaries