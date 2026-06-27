from typing import Any

import re
import unicodedata

import chromadb

from app.core.config import settings
from app.services.embedding_service import EmbeddingService


def normalize_filter_text(
    value: Any,
) -> str:
    """
    Normalize metadata for exact matching.

    Examples:
        "Bong Joon-ho" → "bong joon ho"
        "  Science   Fiction " → "science fiction"
    """
    text = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(
            character
        )
    )

    text = text.casefold()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def split_metadata_values(
    value: Any,
) -> list[str]:
    """
    Convert comma-separated display metadata to normalized values.
    """
    normalized_values: list[str] = []

    for item in str(value or "").split(","):
        normalized = normalize_filter_text(
            item
        )

        if (
            normalized
            and normalized
            not in normalized_values
        ):
            normalized_values.append(
                normalized
            )

    return normalized_values


class MovieVectorStore:
    """
    Chroma wrapper for movie retrieval.

    Every embedding configuration uses a separate collection.
    """

    def __init__(
        self, 
        embedding_service: EmbeddingService | None = None, 
        collection_name: str | None = None,
        reset: bool = False,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.collection_name = collection_name or self.embedding_service.collection_name()

        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_db_dir)
        )

        if reset:
            self.delete_collection_if_exists()

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,  
            metadata={
                "provider": self.embedding_service.provider, 
                "model": self.embedding_service.model_name,
                "dimensions": (
                    self.embedding_service.dimensions
                    if self.embedding_service.dimensions is not None
                    else "default"
                ), 
                "description": (
                    "Movie documents with rich structured metadata"
                ),
            }, 
            configuration={
                "hnsw": {
                    "space": "cosine" # Hierarchical Navigable Small World
                }
            },
        )

    
    def delete_collection_if_exists(self) -> None:
        try:
            self.client.delete_collection(
                name=self.collection_name
            )
            print(
                f"Deleted existing collection: "
                f"{self.collection_name}"
            )
        except Exception:
            # Collection probably did not exist.
            pass


    def count(self) -> int:
        return self.collection.count()


    def upsert_records(
        self,  
        records: list[dict[str, Any]],
    ) -> None:
        if not records:
            return
        
        documents = [
            str(record.get("document") or "") for record in records
        ]

        embeddings = self.embedding_service.embed_texts(documents)

        ids = [
            str(record["movie_id"]) for record in records
        ]

        metadatas = [
            self._build_metadata(record) for record in records
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if self.count() == 0:
            return []
        
        query_embedding = self.embedding_service.embed_query(query)

        # result = self.collection.query(
        #     query_embeddings=[query_embedding],
        #     n_results=min(top_k, self.count()),
        #     include=[
        #         "documents", 
        #         "metadatas", 
        #         "distances",
        #     ],
        # )
        query_arguments: dict[str, Any] = {
            "query_embeddings": [
                query_embedding
            ],
            "n_results": min(
                top_k,
                self.count(),
            ),
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }
        if where:
            query_arguments["where"] = where

        result = self.collection.query(**query_arguments)

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        formatted_results: list[dict[str, Any]] = []

        for movie_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            metadata = metadata or {}
            formatted_results.append({
                "id": str(
                        metadata.get("movie_id", movie_id)
                    ),
                    "title": metadata.get("title", ""),
                    "original_title": metadata.get(
                        "original_title",
                        "",
                    ),
                    "release_year": metadata.get(
                        "release_year",
                        -1,
                    ),

                    "genres": metadata.get("genres", ""),
                    "genres_normalized": metadata.get("genres_normalized", []),
                    "keywords": metadata.get("keywords", ""),
                    "keywords_normalized": metadata.get("keywords_normalized", []),
                    "director": metadata.get("director", ""),
                    "directors_normalized": metadata.get("directors_normalized", []),
                    "cast": metadata.get("cast", ""),
                    "cast_normalized": metadata.get("cast_normalized", []),

                    "runtime": metadata.get("runtime", 0),
                    "original_language": metadata.get(
                        "original_language",
                        "",
                    ),
                    "popularity": metadata.get(
                        "popularity",
                        0.0,
                    ),
                    "vote_average": metadata.get(
                        "vote_average",
                        0.0,
                    ),
                    "vote_count": metadata.get(
                        "vote_count",
                        0,
                    ),
                    "poster_path": metadata.get(
                        "poster_path",
                        ""
                    ),
                    "backdrop_path": metadata.get(
                        "backdrop_path", 
                        ""
                    ),
                    "distance": float(distance),
                    "document": document or "",
            })

        return formatted_results
    
    
    def _build_metadata(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "movie_id": int(record["movie_id"]),
            "title": str(
                record.get("title") or ""
            ),
            "original_title": str(
                record.get("original_title") or ""
            ),
            "release_year": int(
                record.get("release_year") or -1
            ),

            "genres": str(
                record.get("genres") or ""
            ),
            "keywords": str(
                record.get("keywords") or ""
            ),
            "director": str(
                record.get("director") or ""
            ),
            "cast": str(
                record.get("cast") or ""
            ),

            "runtime": int(
                record.get("runtime") or 0
            ),
            "original_language": str(
                record.get(
                    "original_language"
                )
                or ""
            ),

            "popularity": float(
                record.get("popularity") or 0.0
            ),
            "vote_average": float(
                record.get("vote_average") or 0.0
            ),
            "vote_count": int(
                record.get("vote_count") or 0
            ),

            "poster_path": str(
                record.get("poster_path") or ""
            ),
            "backdrop_path": str(
                record.get("backdrop_path") or ""
            ),
        }

        normalized_arrays = {
            "genres_normalized": (
                split_metadata_values(
                    record.get("genres")
                )
            ),
            "keywords_normalized": (
                split_metadata_values(
                    record.get("keywords")
                )
            ),
            "directors_normalized": (
                split_metadata_values(
                    record.get("director")
                )
            ),
            "cast_normalized": (
                split_metadata_values(
                    record.get("cast")
                )
            ),
        }

        # Chroma should not receive empty metadata arrays.
        for key, values in (
            normalized_arrays.items()
        ):
            if values:
                metadata[key] = values

        return metadata