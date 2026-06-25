import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "runs_json",
        type=Path,
        help=(
            "Path to runs.json produced by "
            "run_evaluation.py"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    runs = json.loads(
        args.runs_json.read_text(
            encoding="utf-8"
        )
    )

    query_text: dict[str, str] = {}

    pooled: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    sources: dict[
        tuple[str, str],
        set[str],
    ] = defaultdict(set)

    for run in runs:
        query_id = run["query_id"]
        config_name = run[
            "config_name"
        ]

        query_text[query_id] = run[
            "query"
        ]

        for movie in run.get(
            "results",
            [],
        ):
            movie_id = str(
                movie["movie_id"]
            )

            key = (
                query_id,
                movie_id,
            )

            sources[key].add(
                config_name
            )

            existing = pooled.get(key)

            if (
                existing is None
                or movie["rank"]
                < existing["best_rank"]
            ):
                pooled[key] = {
                    "query_id": query_id,
                    "query": run["query"],
                    "movie_id": movie_id,
                    "title": movie["title"],
                    "best_rank": movie[
                        "rank"
                    ],
                    "genres": ", ".join(
                        movie.get(
                            "genres",
                            [],
                        )
                    ),
                    "director": movie.get(
                        "director",
                        "",
                    ),
                    "runtime": movie.get(
                        "runtime",
                    ),
                    "release_year": (
                        movie.get(
                            "release_year"
                        )
                    ),
                }

    rows: list[dict[str, Any]] = []

    for key, row in pooled.items():
        row = row.copy()

        row["source_configs"] = ", ".join(
            sorted(sources[key])
        )

        # Fill manually:
        # 0 = irrelevant
        # 1 = weak
        # 2 = relevant
        # 3 = excellent
        row["relevance_grade"] = ""
        row["judgment_notes"] = ""

        rows.append(row)

    rows.sort(
        key=lambda row: (
            row["query_id"],
            row["best_rank"],
            row["title"],
        )
    )

    output_path = (
        args.output
        or args.runs_json.parent
        / "judgment_pool.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "query_id",
                "query",
                "movie_id",
                "title",
                "best_rank",
                "source_configs",
                "genres",
                "director",
                "runtime",
                "release_year",
                "relevance_grade",
                "judgment_notes",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Candidate pool written to: "
        f"{output_path}"
    )

    print(
        f"Rows to judge: {len(rows)}"
    )


if __name__ == "__main__":
    main()