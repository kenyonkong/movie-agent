import bisect
import json
from pathlib import Path
from typing import Any


def normalize_text(value: Any) -> str:
    return " ".join(
        str(value or "").casefold().split()
    )


def split_csv(value: Any) -> list[str]:
    return [
        item.strip()
        for item in str(value or "").split(",")
        if item.strip()
    ]


class CatalogIndex:
    """
    In-memory index of the processed JSONL movie catalog.

    It is used only for offline evaluation.
    """

    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(
                f"Movie catalog does not exist: {path}"
            )

        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_title: dict[str, dict[str, Any]] = {}

        popularities: list[float] = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)

                movie_id = str(
                    record.get("movie_id") or ""
                )

                title = str(
                    record.get("title") or ""
                )

                if not movie_id:
                    raise ValueError(
                        "Missing movie_id in catalog on "
                        f"line {line_number}."
                    )

                self.by_id[movie_id] = record

                normalized_title = normalize_text(title)

                if normalized_title:
                    self.by_title[
                        normalized_title
                    ] = record

                popularities.append(
                    float(
                        record.get("popularity")
                        or 0.0
                    )
                )

        self.sorted_popularities = sorted(
            popularities
        )

    def get(
        self,
        movie_id: str | int | None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve by movie ID first and title second.
        """
        if movie_id is not None:
            record = self.by_id.get(
                str(movie_id)
            )

            if record is not None:
                return record

        normalized_title = normalize_text(title)

        if normalized_title:
            record = self.by_title.get(
                normalized_title
            )

            if record is not None:
                return record

        return {}

    def novelty_score(
        self,
        popularity: float,
    ) -> float:
        """
        Convert catalog popularity into a 0–1 novelty proxy.

        A movie more popular than most of the catalog receives low
        novelty. A less popular movie receives high novelty.
        """
        if not self.sorted_popularities:
            return 0.0

        position = bisect.bisect_right(
            self.sorted_popularities,
            float(popularity),
        )

        popularity_percentile = (
            position
            / len(self.sorted_popularities)
        )

        return round(
            1.0 - popularity_percentile,
            4,
        )

    @property
    def count(self) -> int:
        return len(self.by_id)