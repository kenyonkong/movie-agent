from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.services.embedding_service import get_embedding_service

class MovieVectorStore:
    """
    Wrapper around Chroma for movie document vector search.

    This class hides Chroma-specific details from the rest of the app.
    """

    def __init__(self) -> None:
        settings.chroma_db_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_db_dir)
        ) # Use PersistentClient to store data on disk

        self.collection: Collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Movie document embeddings"},
        )

        self.embedding_service = get_embedding_service()
    
    
    def count(self) -> int:
        """
        Return the number of documents in the collection.
        """
        return self.collection.count()
    

    def reset_collection(self) -> None:
        """
        Delete and recreate the Chroma collection.

        Useful when we change the embedding model or document format.
        """
        try:
            self.client.delete_collection(name=settings.chroma_collection_name)
        except Exception:
            pass # Ignore errors if collection doesn't exist

        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Movie document embeddings"},
        )

    
    def add_movies(self, ids: list[str], documents: list[str], metadatas: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
        """
        Add a batch of movie documents to the collection with pre-computed embeddings.

        Args:
            ids: List of unique IDs for each document (e.g. movie IDs)
            documents: List of text content for each document (e.g. movie plot summaries)
            metadatas: List of metadata dicts for each document (e.g. {"title": "Inception", "year": 2010})
            embeddings: List of embedding vectors for each document
        """
        
        if not ids:
            return

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings, 
        )
    

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search for movies semantically similar to a natural-language query.

        Args:
            query: The search query (e.g. "A mind-bending thriller about dreams within dreams")
            top_k: The number of top results to return

        Returns:
            A list of matching documents with their metadata and similarity scores.
        """
        query_embedding = self.embedding_service.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances"],
        )

        formatted_results: list[dict[str, Any]] = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for movie_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            formatted_results.append(
                {
                    "id": movie_id,
                    "title": metadata.get("title"),
                    "release_year": metadata.get("release_year"),
                    "genres": metadata.get("genres"),
                    "distance": distance,
                    "document": document,
                }
            )

        return formatted_results


