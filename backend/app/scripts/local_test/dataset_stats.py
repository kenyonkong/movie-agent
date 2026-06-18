import json
from collections import Counter

import pandas as pd

from app.core.config import settings


def main() -> None:
    movies_path = settings.processed_data_dir / "movies_clean.csv"
    docs_path = settings.processed_data_dir / "movie_documents.jsonl"

    if not movies_path.exists():
        raise FileNotFoundError(f"Missing file: {movies_path}")

    df = pd.read_csv(movies_path)

    print("\n========== DATASET STATS ==========")
    print(f"Movies: {len(df):,}")

    if "release_year" in df.columns:
        print(f"Year range: {int(df['release_year'].min())} - {int(df['release_year'].max())}")

    if "overview" in df.columns:
        missing_overview = df["overview"].isna().sum()
        print(f"Missing overview: {missing_overview:,}")

    if "runtime" in df.columns:
        print(f"Average runtime: {df['runtime'].mean():.2f}")

    if "vote_count" in df.columns:
        print(f"Average vote count: {df['vote_count'].mean():.2f}")
        print(f"Median vote count: {df['vote_count'].median():.2f}")

    if "popularity" in df.columns:
        print(f"Average popularity: {df['popularity'].mean():.2f}")
        print(f"Median popularity: {df['popularity'].median():.2f}")

    if "original_language" in df.columns:
        print("\nTop languages:")
        print(df["original_language"].value_counts().head(15))

    genre_counter: Counter[str] = Counter()

    if "genres_clean" in df.columns:
        for genres_text in df["genres_clean"].fillna(""):
            for genre in str(genres_text).split(","):
                genre = genre.strip()
                if genre:
                    genre_counter[genre] += 1

    print("\nTop genres:")
    for genre, count in genre_counter.most_common(20):
        print(f"{genre}: {count}")

    if docs_path.exists():
        lengths: list[int] = []

        with docs_path.open("r", encoding="utf-8") as file:
            for line in file:
                record = json.loads(line)
                lengths.append(len(record.get("document", "")))

        if lengths:
            print("\nDocument lengths:")
            print(f"Average: {sum(lengths) / len(lengths):.2f}")
            print(f"Min: {min(lengths)}")
            print(f"Max: {max(lengths)}")


if __name__ == "__main__":
    main()