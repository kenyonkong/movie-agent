import argparse
import csv
import json
import statistics
import time
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import MovieVectorStore


DEFAULT_QUERY_PATH = (
    settings.backend_dir
    / "eval"
    / "retrieval_queries.json"
)

DEFAULT_OUTPUT_DIR = (
    settings.backend_dir
    / "eval"
    / "embedding_comparison"
)

MODEL_CONFIGS = [
    {
        "label": "local_minilm",
        "provider": "local",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimensions": None,
    },
    {
        "label": "openai_3_small",
        "provider": "openai",
        "model": "text-embedding-3-small",
        "dimensions": None,
    },
    # Uncomment after building the large index.
    # {
    #     "label": "openai_3_large",
    #     "provider": "openai",
    #     "model": "text-embedding-3-large",
    #     "dimensions": None,
    # },
]

def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def load_queries(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_queries(
    path: Path,
) -> list[dict[str, Any]]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def evaluate_query(
    store: MovieVectorStore,
    query_item: dict[str, Any],
    top_k: int,
    repeats: int,
) -> dict[str, Any]:
    query = query_item["query"]

    durations_ms: list[float] = []
    results: list[dict[str, Any]] = []

    for _ in range(repeats):
        start = time.perf_counter()

        results = store.search(
            query=query,
            top_k=top_k,
        )

        durations_ms.append(
            (time.perf_counter() - start) * 1000
        )

    expected_titles = {
        normalize_title(title)
        for title in query_item["relevant_titles"]
    }

    retrieved_titles = [
        normalize_title(result.get("title", ""))
        for result in results
    ]

    relevant_ranks = [
        rank
        for rank, title in enumerate(
            retrieved_titles,
            start=1,
        )
        if title in expected_titles
    ]

    matching_titles = [
        results[rank - 1]["title"]
        for rank in relevant_ranks
    ]

    hit_at_k = 1 if relevant_ranks else 0

    recall_at_k = (
        len(set(retrieved_titles) & expected_titles)
        / len(expected_titles)
        if expected_titles
        else 0.0
    )

    reciprocal_rank = (
        1.0 / relevant_ranks[0]
        if relevant_ranks
        else 0.0
    )

    return {
        "query_id": query_item["id"],
        "query": query,
        "hit_at_k": hit_at_k,
        "recall_at_k": round(recall_at_k, 4),
        "reciprocal_rank": round(
            reciprocal_rank,
            4,
        ),
        "median_latency_ms": round(
            statistics.median(durations_ms),
            2,
        ),
        "matching_titles": matching_titles,
        "retrieved_titles": [
            result.get("title", "")
            for result in results
        ],
    }


def evaluate_model(
    model_config: dict[str, Any],
    queries: list[dict[str, Any]],
    top_k: int,
    repeats: int,
) -> dict[str, Any]:
    service = EmbeddingService(
        provider=model_config["provider"],
        model_name=model_config["model"],
        dimensions=model_config["dimensions"],
    )

    store = MovieVectorStore(
        embedding_service=service
    )

    if store.count() == 0:
        raise RuntimeError(
            f"Collection is empty: {store.collection_name}"
        )

    # Warm up local model loading and Chroma access.
    # This keeps normal per-query latency separate from cold startup.
    store.search(
        query="movie recommendation warmup",
        top_k=1,
    )

    query_results = [
        evaluate_query(
            store=store,
            query_item=query_item,
            top_k=top_k,
            repeats=repeats,
        )
        for query_item in queries
    ]

    return {
        "label": model_config["label"],
        "provider": service.provider,
        "model": service.model_name,
        "dimensions": service.actual_dimension,
        "collection_name": store.collection_name,
        "collection_count": store.count(),
        "top_k": top_k,
        "query_count": len(query_results),
        "hit_rate_at_k": round(
            statistics.mean(
                item["hit_at_k"]
                for item in query_results
            ),
            4,
        ),
        "mean_recall_at_k": round(
            statistics.mean(
                item["recall_at_k"]
                for item in query_results
            ),
            4,
        ),
        "mean_reciprocal_rank": round(
            statistics.mean(
                item["reciprocal_rank"]
                for item in query_results
            ),
            4,
        ),
        "median_query_latency_ms": round(
            statistics.median(
                item["median_latency_ms"]
                for item in query_results
            ),
            2,
        ),
        "queries": query_results,
    }


def save_outputs(
    reports: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = output_dir / "comparison.json"
    csv_path = output_dir / "summary.csv"

    json_path.write_text(
        json.dumps(
            reports,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "label",
                "provider",
                "model",
                "dimensions",
                "collection_count",
                "hit_rate_at_k",
                "mean_recall_at_k",
                "mean_reciprocal_rank",
                "median_query_latency_ms",
            ],
        )

        writer.writeheader()

        for report in reports:
            writer.writerow(
                {
                    key: report[key]
                    for key in writer.fieldnames
                }
            )

    print(f"\nJSON report: {json_path}")
    print(f"CSV summary: {csv_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERY_PATH,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = load_queries(args.queries)

    reports: list[dict[str, Any]] = []

    for config in MODEL_CONFIGS:
        print("\n" + "=" * 100)
        print(f"Evaluating: {config['label']}")

        try:
            report = evaluate_model(
                model_config=config,
                queries=queries,
                top_k=args.top_k,
                repeats=args.repeats,
            )
        except Exception as error:
            print(
                f"Skipping {config['label']}: {error}"
            )
            continue

        reports.append(report)

        print(
            f"Hit rate@{args.top_k}: "
            f"{report['hit_rate_at_k']:.4f}"
        )
        print(
            f"Recall@{args.top_k}: "
            f"{report['mean_recall_at_k']:.4f}"
        )
        print(
            "MRR: "
            f"{report['mean_reciprocal_rank']:.4f}"
        )
        print(
            "Median query latency: "
            f"{report['median_query_latency_ms']:.2f} ms"
        )

        for item in report["queries"]:
            print(
                f"\n[{item['query_id']}] "
                f"{item['query']}"
            )
            print(
                "Matches: "
                f"{item['matching_titles']}"
            )
            print(
                "Top results: "
                f"{item['retrieved_titles'][:5]}"
            )

    save_outputs(
        reports=reports,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()