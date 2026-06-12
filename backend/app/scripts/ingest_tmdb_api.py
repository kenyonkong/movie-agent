import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

from app.core.config import settings
from app.services.tmdb_client import TMDBClient

RAW_DIR = settings.data_dir / "raw" / "tmdb_api"
PROCESSED_DIR = settings.processed_data_dir

MOVIES_CLEAN_PATH = PROCESSED_DIR / "movies_clean.csv"
MOVIE_DOCUMENTS_PATH = PROCESSED_DIR / "movie_documents.jsonl"
DATASET_STATS_PATH = PROCESSED_DIR / "dataset_stats.json"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    
    text = str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_year(release_date: str | None) -> int | None:
    if not release_date:
        return None
    
    match = re.match(r"^(\d{4})", release_date)

    if not match:
        return None

    return int(match.group(1))


def extract_director(credits: dict[str, Any] | None) -> str:
    if not credits:
        return ""

    crew = credits.get("crew") or []

    names: set[str] = set()

    for person in crew:
        if person.get("job") == "Director":
            name = clean_text(person.get("name"))
            if name:
                names.add(name)

    return ", ".join(sorted(names))


def extract_cast(credits: dict[str, Any] | None, limit: int = 5) -> list[str]:
    if not credits:
        return []
    
    cast = credits.get("cast") or []
    
    names: list[str] = []
    for person in cast[:limit]:
        name = clean_text(person.get("name"))
        if name:
            names.append(name)
    return names


def extract_keywords(keywords_response: dict[str, Any] | None) -> list[str]:
    if not keywords_response:
        return []
    
    keywords = keywords_response.get("keywords") or []

    result: list[str] = []
    
    for item in keywords:
        name = clean_text(item.get("name"))
        if name:
            result.append(name)
    return result


def extract_genres(movie: dict[str, Any]) -> list[str]:
    genres = movie.get("genres") or []
    result: list[str] = []

    for item in genres:
        name = clean_text(item.get("name"))
        if name:
            result.append(name)
    return result


def is_valid_movie(movie: dict[str, Any]) -> bool:
    """
    Filter low-quality or invalid records.

    This keeps the dataset useful for recommendation instead of maximizing size.
    """

    if not movie:
        return False

    if movie.get("adult") is True:
        return False

    if movie.get("video") is True:
        return False

    if movie.get("status") != "Released":
        return False

    title = clean_text(movie.get("title"))
    overview = clean_text(movie.get("overview"))
    release_year = extract_year(movie.get("release_date"))

    if not title:
        return False

    if not overview:
        return False

    if release_year is None:
        return False

    runtime = movie.get("runtime") or 0

    if runtime < 40 or runtime > 240:
        return False

    vote_count = int(movie.get("vote_count") or 0)

    if vote_count < settings.tmdb_min_vote_count:
        return False

    popularity = float(movie.get("popularity") or 0.0)

    if popularity < settings.tmdb_min_popularity:
        return False

    return True


def normalize_movie(movie: dict[str, Any]) -> dict[str, Any]:
    genres = extract_genres(movie)
    cast = extract_cast(movie.get("credits"))
    director = extract_director(movie.get("credits"))
    keywords = extract_keywords(movie.get("keywords"))

    release_date = movie.get("release_date")
    release_year = extract_year(release_date)

    overview = clean_text(movie.get("overview"))
    tagline = clean_text(movie.get("tagline"))

    row = {
        "id": int(movie["id"]),
        "title": clean_text(movie.get("title")),
        "original_title": clean_text(movie.get("original_title")),
        "release_date": release_date,
        "release_year": release_year,
        "genres_clean": ", ".join(genres),
        "overview": overview,
        "tagline": tagline,
        "keywords_clean": ", ".join(keywords),
        "cast_clean": ", ".join(cast),
        "director": director,
        "runtime": int(movie.get("runtime") or 0),
        "vote_average": float(movie.get("vote_average") or 0.0),
        "vote_count": int(movie.get("vote_count") or 0),
        "popularity": float(movie.get("popularity") or 0.0),
        "original_language": clean_text(movie.get("original_language")),
        "status": clean_text(movie.get("status")),
        "homepage": clean_text(movie.get("homepage")),
        "imdb_id": clean_text(movie.get("imdb_id")),
    }

    row["document"] = build_movie_document(row)

    return row


def build_movie_document(row: dict[str, Any]) -> str:
    """
    Build a richer text document for embedding.

    This document is what your vector database searches over.
    """
    parts: list[str] = []

    title = row.get("title") or "Unknown Title"
    year = row.get("release_year")

    if year:
        parts.append(f"Title: {title} ({year})")
    else:
        parts.append(f"Title: {title}")

    if row.get("genres_clean"):
        parts.append(f"Genres: {row['genres_clean']}")

    if row.get("overview"):
        parts.append(f"Overview: {row['overview']}")

    if row.get("tagline"):
        parts.append(f"Tagline: {row['tagline']}")

    if row.get("keywords_clean"):
        parts.append(f"Keywords: {row['keywords_clean']}")

    if row.get("director"):
        parts.append(f"Director: {row['director']}")

    if row.get("cast_clean"):
        parts.append(f"Main cast: {row['cast_clean']}")

    runtime = row.get("runtime")
    if runtime:
        parts.append(f"Runtime: {runtime} minutes")

    vote_average = row.get("vote_average")
    vote_count = row.get("vote_count")
    if vote_average is not None and vote_count is not None:
        parts.append(f"Rating: {vote_average:.1f} based on {vote_count} votes")

    popularity = row.get("popularity")
    if popularity is not None:
        parts.append(f"Popularity: {popularity:.2f}")

    if row.get("original_language"):
        parts.append(f"Original language: {row['original_language']}")

    return "\n".join(parts)


def select_candidate_ids(export_rows: list[dict[str, Any]]) -> list[int]:
    """
    Select candidate IDs from the TMDB daily ID export.

    We over-sample because some IDs will be filtered out after full details
    are fetched.
    """
    candidates: list[dict[str, Any]] = []

    for row in export_rows:
        if row.get("adult") is True:
            continue

        if row.get("video") is True:
            continue

        popularity = float(row.get("popularity") or 0.0)

        if popularity < settings.tmdb_min_popularity:
            continue

        candidates.append(row)

    candidates.sort(
        key=lambda item: float(item.get("popularity") or 0.0),
        reverse=True,
    )

    # Fetch more than needed because many records may be filtered later.
    fetch_limit = int(settings.tmdb_max_movies * 1.5)

    return [int(row["id"]) for row in candidates[:fetch_limit] if row.get("id")]



def deduplicate_movies(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deduplicate by TMDB ID and title/year pair.

    TMDB IDs should already be unique, but title/year dedupe helps avoid
    duplicates from remakes or weird records if they have identical metadata.
    """
    seen_ids: set[int] = set()
    seen_title_year: set[tuple[str, int | None]] = set()

    deduped: list[dict[str, Any]] = []

    for row in rows:
        movie_id = int(row["id"])
        title_key = clean_text(row["title"]).lower()
        year = row.get("release_year")

        title_year_key = (title_key, year)

        if movie_id in seen_ids:
            continue

        if title_year_key in seen_title_year:
            continue

        seen_ids.add(movie_id)
        seen_title_year.add(title_year_key)

        deduped.append(row)

    return deduped


def save_outputs(rows: list[dict[str, Any]]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(MOVIES_CLEAN_PATH, index=False)

    with MOVIE_DOCUMENTS_PATH.open("w", encoding="utf-8") as file:
        for row in rows:
            record = {
                "movie_id": int(row["id"]),
                "title": row["title"],
                "original_title": row.get("original_title", ""),
                "release_year": row["release_year"],

                "genres": row.get("genres_clean", ""),
                "keywords": row.get("keywords_clean", ""),
                "director": row.get("director", ""),
                "cast": row.get("cast_clean", ""),

                "overview": row.get("overview", ""),
                "tagline": row.get("tagline", ""),

                "popularity": float(row["popularity"]),
                "vote_average": float(row["vote_average"]),
                "vote_count": int(row["vote_count"]),
                "runtime": int(row["runtime"]),
                "original_language": row["original_language"],

                "document": row["document"],
            }

            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    stats = build_stats(rows)
    DATASET_STATS_PATH.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved clean CSV: {MOVIES_CLEAN_PATH}")
    print(f"Saved movie documents: {MOVIE_DOCUMENTS_PATH}")
    print(f"Saved dataset stats: {DATASET_STATS_PATH}")


def build_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    genre_counter: Counter[str] = Counter()
    language_counter: Counter[str] = Counter()
    year_counter: Counter[int] = Counter()

    doc_lengths: list[int] = []
    vote_counts: list[int] = []
    popularities: list[float] = []

    for row in rows:
        for genre in str(row.get("genres_clean") or "").split(","):
            genre = genre.strip()
            if genre:
                genre_counter[genre] += 1

        language = row.get("original_language")
        if language:
            language_counter[str(language)] += 1

        year = row.get("release_year")
        if year:
            year_counter[int(year)] += 1

        doc_lengths.append(len(row.get("document") or ""))
        vote_counts.append(int(row.get("vote_count") or 0))
        popularities.append(float(row.get("popularity") or 0.0))

    def average(values: list[int] | list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    return {
        "movie_count": len(rows),
        "top_genres": genre_counter.most_common(20),
        "top_languages": language_counter.most_common(20),
        "year_min": min(year_counter.keys()) if year_counter else None,
        "year_max": max(year_counter.keys()) if year_counter else None,
        "average_document_length": average(doc_lengths),
        "average_vote_count": average(vote_counts),
        "average_popularity": average(popularities),
    }


def main() -> None:
    client = TMDBClient()

    print("Downloading TMDB daily movie ID export...")
    export_path = client.download_recent_movie_id_export(output_dir=RAW_DIR)

    print("Reading export...")
    export_rows = client.read_movie_id_export(export_path)

    print(f"Export rows: {len(export_rows):,}")

    candidate_ids = select_candidate_ids(export_rows) # preliminary filtering out some invalid or low-quality entries

    print(f"Candidate IDs selected: {len(candidate_ids):,}")
    print(f"Target valid movies: {settings.tmdb_max_movies:,}")

    normalized_rows: list[dict[str, Any]] = []

    for movie_id in tqdm(candidate_ids, desc="Fetching TMDB movie details"):
        if len(normalized_rows) >= settings.tmdb_max_movies:
            break

        movie = client.get_movie_details(movie_id) # actual API call to fetch movie details

        if not movie:
            continue

        if not is_valid_movie(movie):
            continue

        row = normalize_movie(movie) # build documents
        normalized_rows.append(row)

    print(f"Fetched valid movies before dedupe: {len(normalized_rows):,}")

    deduped_rows = deduplicate_movies(normalized_rows) # remove duplicate tuple (title, release_year)

    print(f"Movies after dedupe: {len(deduped_rows):,}")

    save_outputs(deduped_rows)

    print("\nDataset upgrade complete.")


if __name__ == "__main__":
    main()