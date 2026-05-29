from abc import ABC, abstractmethod
from typing import Iterable

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from app.core.config import settings

class EmbeddingService(ABC):
    """
    Abstract base class for embedding services.

    This lets the rest of the project use embeddings without caring
    whether they come from OpenAI or a local model.
    """
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Convert a list of texts into a list of embedding vectors.
        """
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        """
        Convert one query string into one embedding vector.
        """
        return self.embed_texts([query])[0]

class OpenAIEmbeddingService(EmbeddingService):
    """
        Embedding service that uses OpenAI's API to generate embeddings.
    """
    
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self.client.embeddings.create(input=texts, model=self.model)

        return [item.embedding for item in response.data]
    
class LocalEmbeddingService(EmbeddingService):
    """
    Embedding service that uses a local SentenceTransformer model to generate embeddings.
    """
    def __init__(self) -> None:
        self.model_name = settings.local_embedding_model
        self.model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        embeddings = self.model.encode(
            texts, 
            batch_size=settings.embedding_batch_size, 
            show_progress_bar=True, 
            normalize_embeddings=True
        )

        if isinstance(embeddings, np.ndarray):
            return embeddings.astype(float).tolist()
        
        return [embedding.tolist() for embedding in embeddings]
    

def get_embedding_service() -> EmbeddingService:
    """
    Factory function that returns the correct embedding service.

    The rest of the code should call this instead of directly creating
    OpenAIEmbeddingService or LocalEmbeddingService.
    """
    provider = settings.embedding_provider.lower().strip()

    if provider == "openai":
        return OpenAIEmbeddingService()

    if provider == "local":
        return LocalEmbeddingService()

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER={settings.embedding_provider}. "
        "Use 'local' or 'openai'."
    )


def batch_items(items: list[str], batch_size: int) -> Iterable[list[str]]:
    """
    Split a list into smaller batches.

    Example:
        [1, 2, 3, 4, 5], batch_size=2
        -> [1, 2], [3, 4], [5]
    """
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]
        # yield in python means this function is a generator that produces batches one at a time,
        # instead of creating all batches in memory at once. This is more efficient for large lists
        # so in this for loop, we calculate the start index of each batch and yield a slice of the list from start to start + batch_size.
        # For example, if items has 1000 elements and batch_size is 100, this will yield 10 batches of 100 elements each, without needing to create a list of all batches in memory at once.