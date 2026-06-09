import json
from pathlib import Path
from typing import Any

from tqdm import tqdm

from app.core.config import settings
from app.services.embedding_service import batch_items, get_embedding_service
from app.services.vector_store import MovieVectorStore

def load_movie_documents(path: Path) -> list[dict[str, Any]]:
    """
    Load movie documents from a JSONL file.

    Each line in the file should be a JSON object with at least "id" and "text" fields.
    """
    if not path.exists():
        raise FileNotFoundError(f"Movie documents file not found at {path}")
    
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    return records


def build_vector_database(reset: bool = True) -> None:
    """
    Build the Chroma vector database from movie documents.
    """
    print("Loading movie documents...")
    records = load_movie_documents(settings.movie_documents_path)

    print(f"Loaded {len(records)} movie documents")

    embedding_service = get_embedding_service()
    vector_store = MovieVectorStore()

    if reset:
        print("Resetting Chroma collection...")
        vector_store.reset_collection()

    batch_size = settings.embedding_batch_size

    print(f"Embedding Provider: {settings.embedding_provider}")
    print(f"Embedding batch size: {batch_size}")
    print("Processing and adding documents to vector store...")

    documents = [record["document"] for record in records]

    for batch_start in tqdm(range(0, len(records), batch_size), desc="Embedding and storing movies"):
        batch_records = records[batch_start:batch_start + batch_size]
        batch_documents = documents[batch_start:batch_start + batch_size]

        embeddings = embedding_service.embed_texts(batch_documents)

        ids = [str(record["movie_id"]) for record in batch_records]

        metadatas = []
        for record in batch_records:
            metadata = {
                "movie_id": int(record["movie_id"]),
                "title": record.get("title", ""),
                "genres": record.get("genres"),
                "popularity": float(record.get("popularity", 0.0) or 0.0),
                "vote_average": float(record.get("vote_average", 0.0) or 0.0),
                "vote_count": int(record.get("vote_count", 0) or 0),
            }

            release_year = record.get("release_year")
            if release_year is not None:
                metadata["release_year"] = int(release_year)
            else:
                metadata["release_year"] = -1
            
            metadatas.append(metadata)
        
        vector_store.add_movies(
            ids=ids,
            documents=batch_documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
    
    print("\nVector database build complete.")
    print(f"Chroma path: {settings.chroma_db_dir}")
    print(f"Collection name: {settings.chroma_collection_name}")
    print(f"Total stored movies: {vector_store.count()}")


def main() -> None:
    build_vector_database(reset=True)


if __name__ == "__main__":
    main()