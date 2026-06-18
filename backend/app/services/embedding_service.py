import re
import time
from typing import Any

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from app.core.config import settings

class EmbeddingService:
    """
    Pluggable embedding service.

    Supported providers:
    - local: SentenceTransformers
    - openai: OpenAI Embeddings API

    The rest of the recommendation pipeline does not need to know
    which provider generated the vectors.
    """

    def __init__(
        self, 
        provider: str | None = None, 
        model_name: str | None = None, 
        dimensions: int | None = None
    ) -> None:
        self.provider = (
            provider or settings.embedding_provider
        ).strip().lower()

        self.batch_size = settings.embedding_batch_size
        self.total_input_tokens = 0
        self._actual_dimension: int | None = None

        self.local_model: SentenceTransformer | None = None
        self.openai_client: OpenAI | None = None

        if self.provider == "local":
            self.model_name = model_name or settings.local_embedding_model
            if dimensions is not None:
                raise ValueError(
                    "The dimensions option is only supported for the "
                    "OpenAI embedding provider."
                )
            self.dimensions = None
            self.local_model = SentenceTransformer(self.model_name)

            dimension = self.local_model.get_embedding_dimension()
            if dimension is not None:
                self._actual_dimension = dimension
        
        elif self.provider == "openai":
            self.model_name = model_name or settings.openai_embedding_model
            self.dimensions = (
                dimensions
                if dimensions is not None
                else settings.openai_embedding_dimensions
            )
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY is required when "
                    "EMBEDDING_PROVIDER=openai."
                )
            self.openai_client = OpenAI(api_key=settings.openai_api_key)

        else:
            raise ValueError(
                "Unsupported embedding provider: "
                f"{self.provider!r}. Use 'local' or 'openai'."
            )
        
    
    @property
    def actual_dimension(self) -> int | None:
        return self._actual_dimension
    
    @property
    def model_identifier(self) -> str:
        """
        Human-readable identifier used in reports.
        """
        if self.dimensions is not None:
            return (
                f"{self.provider}:{self.model_name}:"
                f"dimensions={self.dimensions}"
            )

        return f"{self.provider}:{self.model_name}"
    

    def collection_name(self, prefix: str | None = None) -> str:
        """
        Create a valid deterministic Chroma collection name.

        Examples:
        movie-docs-local-sentence-transformers-all-minilm-l6-v2
        movie-docs-openai-text-embedding-3-small-default
        """
        if settings.chroma_collection_name:
            return settings.chroma_collection_name
        
        collection_prefix = prefix or settings.chroma_collection_prefix

        raw_name = (
            f"{collection_prefix}-"
            f"{self.provider}-"
            f"{self.model_name}"
        )

        if self.provider == "openai":
            dimension_label = (
                str(self.dimensions)
                if self.dimensions is not None
                else "default"
            )
            raw_name += f"-d{dimension_label}"

        normalized = raw_name.lower()
        normalized = re.sub(r"[^a-z0-9._-]+", "-", normalized)
        normalized = re.sub(r"-+", "-", normalized)
        normalized = normalized.strip("-._")

        if len(normalized) < 3:
            normalized = f"movie-{normalized}"

        return normalized[:512].rstrip("-._")
    

    def embed_texts(
            self, 
            texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []
        
        cleaned_texts = [
            self._clean_text(text) for text in texts
        ]

        if self.provider == "local":
            return self._embed_local(cleaned_texts)

        return self._embed_openai(cleaned_texts)
    

    def embed_query(self, query: str) -> list[float]:
        embeddings = self.embed_texts([query])
        if not embeddings:
            raise RuntimeError("Embedding service returned no query vector.")
        
        return embeddings[0]
    

    def _embed_local(
        self, 
        texts: list[str], 
    ) -> list[list[float]]:
        if self.local_model is None:
            raise RuntimeError("Local embedding model is not initialized.")
        
        embeddings = self.local_model.encode(
            texts, 
            batch_size=self.batch_size, 
            show_progress_bar=False, 
            convert_to_numpy=True, 
            normalize_embeddings=True,
        )
        
        result = embeddings.tolist()
        if result and self._actual_dimension is None:
            self._actual_dimension = len(result[0])
        
        return result
    

    def _embed_openai(
        self, 
        texts: list[str], 
        max_retries: int = 5,
    ) -> list[list[float]]:
        if self.openai_client is None:
            raise RuntimeError("OpenAI embedding client is not initialized.")
        
        response_args: dict[str, Any] = {
            "model": self.model_name, 
            "input": texts,
            "encoding_format": "float",
        }

        if self.dimensions is not None:
            response_args["dimensions"] = self.dimensions

        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = self.openai_client.embeddings.create(**response_args)
                
                ordered_items = sorted(
                    response.data,
                    key=lambda item: item.index,
                )

                embeddings = [
                    item.embedding
                    for item in ordered_items
                ]

                if embeddings and self._actual_dimension is None:
                    self._actual_dimension = len(embeddings[0])
                
                usage = getattr(response, "usage", None)
                if usage is not None:
                    total_tokens = getattr(usage, "total_tokens", 0)
                    self.total_input_tokens += int(total_tokens or 0)

                return embeddings

            except Exception as e:
                last_error = e
                if attempt == max_retries - 1:
                    break

                sleep_seconds = min(2 ** attempt, 30)
                print(
                    "Embedding request failed. "
                    f"Retrying in {sleep_seconds}s: {e}"
                )
                time.sleep(sleep_seconds)
            
        raise RuntimeError(
            "OpenAI embedding request failed after "
            f"{max_retries} attempts: {last_error}"
        )
    

    def _clean_text(self, text: str) -> str:
        # Remove extra whitespace and newlines
        return " ".join((text or "").split())