import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "pool_csv",
        type=Path,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    judgments: dict[
        str,
        dict[str, int],
    ] = {}

    skipped = 0
    imported = 0

    with args.pool_csv.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            grade_text = str(
                row.get(
                    "relevance_grade",
                    "",
                )
            ).strip()

            if not grade_text:
                skipped += 1
                continue

            grade = int(grade_text)

            if grade not in {
                0,
                1,
                2,
                3,
            }:
                raise ValueError(
                    "Relevance grades must be "
                    f"0–3. Received {grade} for "
                    f"{row.get('title')}."
                )

            query_id = str(
                row["query_id"]
            )

            movie_id = str(
                row["movie_id"]
            )

            judgments.setdefault(
                query_id,
                {},
            )[movie_id] = grade

            imported += 1

    args.output.write_text(
        json.dumps(
            judgments,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Imported judgments: "
        f"{imported}"
    )

    print(
        f"Skipped unlabeled rows: "
        f"{skipped}"
    )

    print(
        f"Output: {args.output}"
    )


if __name__ == "__main__":
    main()