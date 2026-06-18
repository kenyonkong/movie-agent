import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tqdm import tqdm

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import MovieVectorStore

MANIFEST_DIR = settings.backend_dir / "eval" / "embedding_indexes"

def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Movie document file does not exist: {path}"
        )
    
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            if not record.get("movie_id"):
                raise ValueError(
                    f"Missing movie_id on line {line_number}"
                )

            if not record.get("document"):
                raise ValueError(
                    f"Missing document on line {line_number}"
                )

            records.append(record)

    return records


def save_manifest(
    service: EmbeddingService,
    store: MovieVectorStore, 
    record_count: int, 
    elapsed_seconds: float,
) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "built_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "provider": service.provider,
        "model": service.model_name,
        "requested_dimensions": service.dimensions,
        "actual_dimensions": service.actual_dimension,
        "collection_name": store.collection_name,
        "record_count": record_count,
        "collection_count": store.count(),
        "build_seconds": round(elapsed_seconds, 2),
        "openai_input_tokens": service.total_input_tokens,
        "dataset_path": str(
            settings.movie_documents_path
        ),
    }

    output_path = (
        MANIFEST_DIR
        / f"{store.collection_name}.json"
    )


    output_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build one Chroma movie index for a specific "
            "embedding provider/model."
        )
    )

    parser.add_argument(
        "--provider",
        choices=["local", "openai"],
        default=None,
    )

    parser.add_argument(
        "--model",
        default=None,
    )
    
    parser.add_argument(
        "--dimensions",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--reset", 
        action="store_true",
        help="Delete only this model's collection before rebuilding.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    service = EmbeddingService(
        provider=args.provider,
        model_name=args.model,
        dimensions=args.dimensions,
    )

    if args.batch_size is not None:
        service.batch_size = args.batch_size
    
    store = MovieVectorStore(
        embedding_service=service, 
        reset=args.reset, 
    )

    records = load_records(settings.movie_documents_path)

    print("\n========== EMBEDDING BUILD ==========")
    print(f"Provider: {service.provider}")
    print(f"Model: {service.model_name}")
    print(f"Dimensions requested: {service.dimensions}")
    print(f"Collection: {store.collection_name}")
    print(f"Records: {len(records):,}")
    print(f"Batch size: {service.batch_size}")

    if service.local_model is not None:
        print(
            "Local max sequence length: "
            f"{service.local_model.max_seq_length}"
        )

    start_time = time.perf_counter()

    for start in tqdm(
        range(0, len(records), service.batch_size),
        desc=f"Building {store.collection_name}",
    ):
        batch = records[start:start + service.batch_size]
        store.upsert_records(batch)
    
    elapsed_seconds = time.perf_counter() - start_time

    manifest_path = save_manifest(
        service=service,
        store=store,
        record_count=len(records),
        elapsed_seconds=elapsed_seconds,
    )   
    
    print("\n========== BUILD COMPLETE ==========")
    print(f"Collection count: {store.count():,}")
    print(
        f"Actual vector dimensions: "
        f"{service.actual_dimension}"
    )
    print(
        f"Elapsed: {elapsed_seconds:.2f} seconds"
    )

    if service.provider == "openai":
        print(
            "OpenAI input tokens reported: "
            f"{service.total_input_tokens:,}"
        )

    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
    
