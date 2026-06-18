import statistics
import time

from app.services.vector_store import MovieVectorStore


QUERIES = [
    "lonely gentle futuristic romance",
    "dark psychological thriller with mystery",
    "funny family animated adventure",
    "epic fantasy world with battles",
    "quiet emotional drama about memory",
    "fast paced action movie with spies",
    "beautiful coming of age story",
    "space exploration science fiction",
]


def main() -> None:
    vector_store = MovieVectorStore()

    if vector_store.count() == 0:
        raise RuntimeError(
            "Vector database is empty. Run: python -m app.scripts.build_embeddings"
        )

    latencies_ms: list[float] = []

    print("\n========== SEARCH LATENCY BENCHMARK ==========")

    for query in QUERIES:
        start = time.perf_counter()
        results = vector_store.search(query, top_k=5)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies_ms.append(latency_ms)

        top_title = results[0]["title"] if results else "N/A"

        print(
            f"Query: {query}\n"
            f"  Latency: {latency_ms:.2f} ms\n"
            f"  Top result: {top_title}"
        )

    print("\n========== SUMMARY ==========")
    print(f"Average latency: {statistics.mean(latencies_ms):.2f} ms")
    print(f"Median latency: {statistics.median(latencies_ms):.2f} ms")
    print(f"Min latency: {min(latencies_ms):.2f} ms")
    print(f"Max latency: {max(latencies_ms):.2f} ms")


if __name__ == "__main__":
    main()