from app.services.vector_store import MovieVectorStore


TEST_QUERIES = [
    {
        "query": "lonely gentle futuristic romance like Her",
        "expected_keywords": ["romance", "science fiction", "future", "love"],
    },
    {
        "query": "dark psychological thriller with obsession and mystery",
        "expected_keywords": ["thriller", "mystery", "crime", "psychological"],
    },
    {
        "query": "epic fantasy adventure with magic and battles",
        "expected_keywords": ["fantasy", "adventure", "magic"],
    },
    {
        "query": "funny family friendly animated movie",
        "expected_keywords": ["animation", "family", "comedy"],
    },
]


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def main() -> None:
    vector_store = MovieVectorStore()

    if vector_store.count() == 0:
        raise RuntimeError(
            "Vector database is empty. Run: python -m app.scripts.build_embeddings"
        )

    print("\n========== RETRIEVAL SMOKE TEST ==========")
    print(f"Stored movies: {vector_store.count()}")

    total = 0
    matched = 0

    for item in TEST_QUERIES:
        query = item["query"]
        expected_keywords = item["expected_keywords"]

        print("\n" + "=" * 80)
        print(f"Query: {query}")
        print(f"Expected keywords: {expected_keywords}")

        results = vector_store.search(query, top_k=5)

        query_matched = False

        for rank, result in enumerate(results, start=1):
            combined_text = " ".join(
                [
                    str(result.get("title", "")),
                    str(result.get("genres", "")),
                    str(result.get("document", "")),
                ]
            )

            hit = contains_any_keyword(combined_text, expected_keywords)
            query_matched = query_matched or hit

            marker = "HIT" if hit else "MISS"

            print(
                f"{rank}. {result.get('title')} "
                f"({result.get('release_year')}) "
                f"[{result.get('genres')}] "
                f"distance={result.get('distance'):.4f} "
                f"{marker}"
            )

        total += 1
        matched += int(query_matched)

    print("\n========== SUMMARY ==========")
    print(f"Queries with at least one keyword hit in top 5: {matched}/{total}")


if __name__ == "__main__":
    main()