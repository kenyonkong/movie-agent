import csv
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from app.core.config import settings
from app.db.schemas import MovieSearchItem


@dataclass(frozen=True)
class _CatalogMovie:
    normalized_title: str
    popularity: float
    item: MovieSearchItem


class MovieCatalogService:
    """Load the local movie catalog and search its title field."""

    TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
    TMDB_BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w780"

    def __init__(self, catalog_path: Path | None = None) -> None:
        self.catalog_path = catalog_path or settings.movies_clean_path
        self._movies: list[_CatalogMovie] | None = None
        self._load_lock = Lock()

    def search(
        self,
        title_query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MovieSearchItem], int]:
        """Return case-insensitive title matches and the total match count."""
        normalized_query = self._normalize_title(title_query)

        if not normalized_query:
            return [], 0

        matches = [
            movie
            for movie in self._get_movies()
            if normalized_query in movie.normalized_title
        ]
        matches.sort(key=self._popularity_sort_key)

        total = len(matches)
        page = matches[offset : offset + limit]
        return [movie.item for movie in page], total

    def _get_movies(self) -> list[_CatalogMovie]:
        if self._movies is None:
            with self._load_lock:
                if self._movies is None:
                    self._movies = self._load_movies()

        return self._movies

    def _load_movies(self) -> list[_CatalogMovie]:
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                "Movie catalog was not found at "
                f"{self.catalog_path}. Run the movie ingestion step first."
            )

        movies: list[_CatalogMovie] = []

        with self.catalog_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as catalog_file:
            reader = csv.DictReader(catalog_file)

            for row in reader:
                title = self._optional_string(row.get("title"))
                movie_id = self._optional_string(row.get("id"))

                if title is None or movie_id is None:
                    continue

                item = MovieSearchItem(
                    movie_id=movie_id,
                    title=title,
                    release_year=self._optional_int(
                        row.get("release_year")
                    ),
                    director=self._optional_string(
                        row.get("director")
                    ),
                    cast=self._parse_cast(row.get("cast_clean")),
                    movie_rating=self._optional_float(
                        row.get("vote_average")
                    ),
                    poster_url=self._build_image_url(
                        self.TMDB_POSTER_BASE_URL,
                        row.get("poster_path"),
                    ),
                    backdrop_url=self._build_image_url(
                        self.TMDB_BACKDROP_BASE_URL,
                        row.get("backdrop_path"),
                    ),
                )
                movies.append(
                    _CatalogMovie(
                        normalized_title=self._normalize_title(title),
                        popularity=(
                            self._optional_float(row.get("popularity"))
                            or 0.0
                        ),
                        item=item,
                    )
                )

        return movies

    def _popularity_sort_key(
        self,
        movie: _CatalogMovie,
    ) -> tuple[float, str, int]:
        release_year = movie.item.release_year or 0
        return (
            -movie.popularity,
            movie.normalized_title,
            -release_year,
        )

    @staticmethod
    def _normalize_title(value: str) -> str:
        return " ".join(value.split()).casefold()

    @staticmethod
    def _optional_string(value: str | None) -> str | None:
        if value is None:
            return None

        text = value.strip()
        return text or None

    @staticmethod
    def _optional_int(value: str | None) -> int | None:
        if value is None or not value.strip():
            return None

        try:
            return int(float(value))
        except ValueError:
            return None

    @staticmethod
    def _optional_float(value: str | None) -> float | None:
        if value is None or not value.strip():
            return None

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_cast(value: str | None) -> list[str]:
        if value is None:
            return []

        return [
            name.strip()
            for name in value.split(",")
            if name.strip()
        ]

    @staticmethod
    def _build_image_url(
        base_url: str,
        image_path: str | None,
    ) -> str | None:
        if image_path is None:
            return None

        path = image_path.strip()

        if not path:
            return None

        if not path.startswith("/"):
            path = f"/{path}"

        return f"{base_url}{path}"
