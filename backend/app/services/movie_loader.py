import ast
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

MOVIES_RAW_PATH = RAW_DATA_DIR / "movies_metadata.csv" # / is used to join paths in pathlib
CREDITS_RAW_PATH = RAW_DATA_DIR / "credits.csv"

MOVIES_CLEAN_PATH = PROCESSED_DATA_DIR / "movies_clean.csv"
MOVIE_DOCUMENTS_PATH = PROCESSED_DATA_DIR / "movies_documents.jsonl"


def safe_parse_list(value: Any) -> list[dict[str, Any]]:
    """
    Parse a string that looks like a Python/JSON list of dictionaries.

    Example input:
        '[{"id": 18, "name": "Drama"}]'

    Output:
        [{"id": 18, "name": "Drama"}]

    If parsing fails, return an empty list.
    """
    if value is None or pd.isna(value):
        return []
    
    if isinstance(value, list):
        return value
    
    if not isinstance(value, str):
        return []
    
    value = value.strip()

    if value == "":
        return []
    
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return parsed
        return []
    except (ValueError, SyntaxError):
        return []


def extract_names(value: Any, max_items: int | None = None) -> list[str]:
    """
    Extract the 'name' field from a list of dictionaries.

    Example input:
        '[{"id": 18, "name": "Drama"}, {"id": 35, "name": "Comedy"}]'

    Output:
        ["Drama", "Comedy"]

    If parsing fails, return an empty list.
    """
    items = safe_parse_list(value)
    names: list[str] = []
    
    for item in items:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    
    if max_items is not None:
        names = names[:max_items]
    return names


def extract_director(crew_value: Any) -> str | None:
    """
    Extract director name from the crew column.

    The crew column contains many people with different jobs.
    We only want the person whose job is 'Director'.
    """
    crew = safe_parse_list(crew_value)
    
    for person in crew:
        if not isinstance(person, dict):
            continue
            
        job = person.get("job")
        name = person.get("name")
        if job == "Director" and isinstance(name, str) and name.strip():
            return name.strip()
    
    return ""


def clean_text(value: Any) -> str:
    """
    Normalize text fields.

    This removes extra spaces and handles missing values.
    """
    if value is None or pd.isna(value):
        return ""
    
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_year(release_date: Any) -> int | None:
    """
    Extract the year from the release date.

    The release date is in the format "YYYY-MM-DD".
    We want to extract just the year as an integer.
    """
    if release_date is None or pd.isna(release_date):
        return None
    
    release_date = str(release_date).strip()
    
    if len(release_date) < 4:
        return None
    
    year_text = release_date[:4]

    if not year_text.isdigit():
        return None
    
    return int(year_text)


def build_movie_document(row: pd.Series) -> str:
    """
    Build the embedding-ready text representation for one movie.

    This text will later be converted into an embedding.
    The better this text is, the better semantic search will be.
    """
    parts: list[str] = []

    title = clean_text(row.get("title", ""))
    year = row.get("release_year")
    overview = clean_text(row.get("overview", ""))
    tagline = clean_text(row.get("tagline", ""))
    genres = row.get("genres_clean", "")
    keywords = row.get("keywords_clean", "")
    cast = row.get("cast_clean", "")
    director = clean_text(row.get("director", ""))
    runtime = row.get("runtime")
    vote_average = row.get("vote_average")
    popularity = row.get("popularity")

    if title:
        if pd.notna(year):
            parts.append(f"Title: {title} ({int(year)})")
        else:
            parts.append(f"Title: {title}")

    if genres:
        parts.append(f"Genres: {genres}")

    if overview:
        parts.append(f"Overview: {overview}")

    if tagline:
        parts.append(f"Tagline: {tagline}")

    if keywords:
        parts.append(f"Keywords and themes: {keywords}")

    if cast:
        parts.append(f"Main cast: {cast}")

    if director:
        parts.append(f"Director: {director}")

    if pd.notna(runtime):
        parts.append(f"Runtime: {int(runtime)} minutes")

    if pd.notna(vote_average):
        parts.append(f"Average rating: {float(vote_average):.1f}")

    if pd.notna(popularity):
        parts.append(f"Popularity score: {float(popularity):.1f}")

    return "\n".join(parts)


def load_and_clean_movies() -> pd.DataFrame:
    """
    Load raw TMDB movie and credits data, clean important fields,
    merge them, and return one clean dataframe.
    """
    if not MOVIES_RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing {MOVIES_RAW_PATH}. "
            "Please place the TMDB movies CSV at backend/data/raw/movies_metadata.csv"
        )

    if not CREDITS_RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CREDITS_RAW_PATH}. "
            "Please place the TMDB credits CSV at backend/data/raw/credits.csv"
        )

    movies = pd.read_csv(MOVIES_RAW_PATH)
    credits = pd.read_csv(CREDITS_RAW_PATH)

    # Normalize IDs so the merge works.
    movies["id"] = pd.to_numeric(movies["id"], errors="coerce") # if there are non-numeric IDs, they will become NaN, if NaN, others will be float
    credits["movie_id"] = pd.to_numeric(credits["movie_id"], errors="coerce")

    movies = movies.dropna(subset=["id"])
    credits = credits.dropna(subset=["movie_id"])

    movies["id"] = movies["id"].astype(int)
    credits["movie_id"] = credits["movie_id"].astype(int)

    merged = movies.merge(
        credits[["movie_id", "cast", "crew"]], # select only the columns we need
        left_on="id", # merge on movies.id and credits.movie_id,
        right_on="movie_id",
        how="left", # left join to keep all movies, even those without credits info
    )

    # Clean basic text fields.
    merged["title"] = merged["title"].apply(clean_text) # .apply applies the function to each element in the column
    merged["overview"] = merged["overview"].apply(clean_text)
    merged["tagline"] = merged["tagline"].apply(clean_text)

    # Extract structured features from JSON-like columns.
    merged["genres_list"] = merged["genres"].apply(extract_names)
    merged["keywords_list"] = merged["keywords"].apply(lambda x: extract_names(x, max_items=12))
    merged["cast_list"] = merged["cast"].apply(lambda x: extract_names(x, max_items=5))
    merged["director"] = merged["crew"].apply(extract_director)

    # Convert lists into readable strings for CSV and embedding text.
    merged["genres_clean"] = merged["genres_list"].apply(lambda x: ", ".join(x)) # join the list of genres into a single string separated by commas
    merged["keywords_clean"] = merged["keywords_list"].apply(lambda x: ", ".join(x))
    merged["cast_clean"] = merged["cast_list"].apply(lambda x: ", ".join(x))

    merged["release_year"] = merged["release_date"].apply(extract_year)

    # Numeric cleaning.
    numeric_columns = ["runtime", "vote_average", "vote_count", "popularity"]
    for col in numeric_columns:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")

    # Keep only useful columns for our project.
    clean_columns = [
        "id",
        "title",
        "release_year",
        "overview",
        "tagline",
        "genres_clean",
        "keywords_clean",
        "cast_clean",
        "director",
        "runtime",
        "vote_average",
        "vote_count",
        "popularity",
    ]

    clean_df = merged[clean_columns].copy()

    # Remove movies with no title or no overview.
    # For semantic recommendation, movies without overview are usually weak.
    clean_df = clean_df[
        (clean_df["title"].str.len() > 0)
        & (clean_df["overview"].str.len() > 0)
    ]

    # Remove duplicate movie IDs.
    clean_df = clean_df.drop_duplicates(subset=["id"])

    # Build document text.
    tqdm.pandas(desc="Building movie documents")
    clean_df["document"] = clean_df.progress_apply(build_movie_document, axis=1)

    # Sort for stable output.
    clean_df = clean_df.sort_values(by=["release_year", "title"], ascending=[False, True])

    return clean_df.reset_index(drop=True)


def save_processed_movies(clean_df: pd.DataFrame) -> None:
    """
    Save cleaned movie data to CSV and movie documents to JSONL.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    clean_df.to_csv(MOVIES_CLEAN_PATH, index=False)

    with MOVIE_DOCUMENTS_PATH.open("w", encoding="utf-8") as f:
        for _, row in clean_df.iterrows():
            record = {
                "movie_id": int(row["id"]),
                "title": row["title"],
                "release_year": (
                    int(row["release_year"]) if pd.notna(row["release_year"]) else None
                ), 
                "genres": row["genres_clean"],
                "document": row["document"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def preview_movies(clean_df: pd.DataFrame, n: int = 3) -> None:
    """
    Print a few examples so we can manually inspect quality.
    """
    print("\n========== DATASET SUMMARY ==========")
    print(f"Number of cleaned movies: {len(clean_df)}")
    print(f"Columns: {list(clean_df.columns)}")

    print("\n========== SAMPLE MOVIE DOCUMENTS ==========")

    sample_df = clean_df.sample(n=min(n, len(clean_df)), random_state=42)

    for _, row in sample_df.iterrows():
        print("\n----------------------------------------")
        print(row["document"])