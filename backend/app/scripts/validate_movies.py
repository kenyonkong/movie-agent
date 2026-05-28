from pathlib import Path

import pandas as pd


PROCESSED_PATH = Path("data/processed/movies_clean.csv")


def main() -> None:
    if not PROCESSED_PATH.exists():
        raise FileNotFoundError(
            "movies_clean.csv not found. Run: python -m app.scripts.ingest_movies"
        )

    df = pd.read_csv(PROCESSED_PATH)

    print("\n========== VALIDATION REPORT ==========")
    print(f"Total movies: {len(df)}")

    required_columns = [
        "id",
        "title",
        "overview",
        "genres_clean",
        "director",
        "document",
    ]

    print("\nMissing values:")
    for col in required_columns:
        missing = df[col].isna().sum()
        pct = missing / len(df) * 100
        print(f"  {col}: {missing} missing ({pct:.2f}%)")

    duplicate_ids = df["id"].duplicated().sum()
    print(f"\nDuplicate movie IDs: {duplicate_ids}")

    avg_doc_length = df["document"].astype(str).str.len().mean()
    min_doc_length = df["document"].astype(str).str.len().min()
    max_doc_length = df["document"].astype(str).str.len().max()

    print("\nDocument length:")
    print(f"  Average characters: {avg_doc_length:.1f}")
    print(f"  Min characters: {min_doc_length}")
    print(f"  Max characters: {max_doc_length}")

    movies_without_genres = (df["genres_clean"].fillna("").str.len() == 0).sum()
    print(f"\nMovies without genres: {movies_without_genres}")

    print("\nTop 10 genres:")
    genre_counts: dict[str, int] = {}

    for genres in df["genres_clean"].fillna(""):
        for genre in genres.split(","):
            genre = genre.strip()
            if genre:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

    for genre, count in sorted(
        genre_counts.items(), key=lambda item: item[1], reverse=True
    )[:10]:
        print(f"  {genre}: {count}")

    print("\nValidation completed.")


if __name__ == "__main__":
    main()