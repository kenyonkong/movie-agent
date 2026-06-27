from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.vector_store import (
    MovieVectorStore,
)


def print_results(
    title: str,
    results: list[dict],
) -> None:
    print("\n" + "=" * 100)
    print(title)

    for index, movie in enumerate(
        results,
        start=1,
    ):
        print(
            f"{index}. "
            f"{movie['title']} "
            f"({movie['release_year']}) "
            f"director={movie['director']} "
            f"runtime={movie['runtime']}"
        )


def main() -> None:
    embedding_service = EmbeddingService()

    store = MovieVectorStore(
        embedding_service=(
            embedding_service
        )
    )

    nolan_results = store.search(
        query=(
            "dreams memory identity time"
        ),
        top_k=10,
        where={
            "$and": [
                {
                    "directors_normalized": {
                        "$contains": (
                            "christopher nolan"
                        )
                    }
                },
                {
                    "runtime": {
                        "$lte": 149
                    }
                },
            ]
        },
    )

    print_results(
        "Christopher Nolan under 150 minutes",
        nolan_results,
    )

    korean_results = store.search(
        query=(
            "moral ambiguity social tension"
        ),
        top_k=10,
        where={
            "$and": [
                {
                    "original_language": {
                        "$eq": "ko"
                    }
                },
                {
                    "genres_normalized": {
                        "$contains": "thriller"
                    }
                },
                {
                    "release_year": {
                        "$gte": 2001
                    }
                },
            ]
        },
    )

    print_results(
        "Korean thrillers after 2000",
        korean_results,
    )


if __name__ == "__main__":
    main()