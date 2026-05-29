import argparse

from app.services.vector_store import MovieVectorStore

def print_result(index: int, result: dict) -> None:
    print("\n" + "=" * 80)
    print(f"Rank {index}")
    print(f"Title: {result.get('title')}")
    print(f"Year: {result.get('release_year')}")
    print(f"Genres: {result.get('genres')}")
    print(f"Distance: {result.get('distance'):.4f}")

    document = result.get("document", "")
    preview = document[:700]

    print(f"\nDocument preview:")
    print(preview)

    if len(document) > len(preview):
        print("... [truncated]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search movies using semantic vector search."
    )

    parser.add_argument(
        "query", 
        type=str, 
        help="Natural-language movie search query."
    )

    parser.add_argument(
        "--top-k", 
        type=int, 
        default=5, 
        help="Number of top results to return"
    )

    args = parser.parse_args()

    vector_store = MovieVectorStore()
    
    if vector_store.count() == 0:
        raise ValueError("No movies found in vector store. Please run build_embeddings.py first to create the vector database.")

    print(f"\nQuery: {args.query}")
    print(f"Top K: {args.top_k}")
    print(f"Stored movies in vector store: {vector_store.count()}")

    results = vector_store.search(args.query, top_k=args.top_k)

    for index, result in enumerate(results, start=1):
        print_result(index, result)


if __name__ == "__main__":
    main()
    