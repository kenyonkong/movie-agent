import argparse
import json
from pathlib import Path

import tiktoken

from app.core.config import settings

MODEL_PRICES_PER_MILLION = {
    "text-embedding-3-small": 0.02,
    "text-embedding-3-large": 0.13,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=settings.movie_documents_path,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        encoding = tiktoken.encoding_for_model(
            args.model
        )
    except KeyError:
        encoding = tiktoken.get_encoding(
            "cl100k_base"
        )

    document_count = 0
    total_tokens = 0
    maximum_tokens = 0
    oversized_documents = 0

    with args.path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)
            document = str(
                record.get("document") or ""
            )

            token_count = len(
                encoding.encode(document)
            )

            document_count += 1
            total_tokens += token_count
            maximum_tokens = max(
                maximum_tokens,
                token_count,
            )

            if token_count > 8192:
                oversized_documents += 1

    average_tokens = (
        total_tokens / document_count
        if document_count
        else 0.0
    )

    price = MODEL_PRICES_PER_MILLION.get(
        args.model
    )

    print("\n========== EMBEDDING COST ESTIMATE ==========")
    print(f"Model: {args.model}")
    print(f"Documents: {document_count:,}")
    print(f"Total estimated tokens: {total_tokens:,}")
    print(f"Average tokens/document: {average_tokens:.2f}")
    print(f"Maximum document tokens: {maximum_tokens:,}")
    print(
        f"Documents above 8192 tokens: "
        f"{oversized_documents:,}"
    )

    if price is None:
        print(
            "No price configured. Check the official "
            "OpenAI pricing page."
        )
        return

    estimated_cost = (
        total_tokens
        / 1_000_000
        * price
    )

    print(
        f"Configured price: ${price:.4f} "
        "per 1M input tokens"
    )
    print(
        f"Estimated one-time build cost: "
        f"${estimated_cost:.4f}"
    )


if __name__ == "__main__":
    main()