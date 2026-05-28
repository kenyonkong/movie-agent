from app.services.movie_loader import (
    load_and_clean_movies,
    preview_movies,
    save_processed_movies,
)


def main() -> None:
    print("Starting movie data ingestion...")

    clean_df = load_and_clean_movies()

    save_processed_movies(clean_df)

    preview_movies(clean_df, n=5)

    print("\nSaved processed files:")
    print("  - data/processed/movies_clean.csv")
    print("  - data/processed/movie_documents.jsonl")
    print("\nMovie data ingestion completed successfully.")


if __name__ == "__main__":
    main()