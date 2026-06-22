import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv() # Load environment variables from .env file


def optional_int_from_env(name: str) -> int | None:
    value = os.getenv(name)

    if value is None or not value.strip():
        return None

    return int(value)

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Movie Agent API")
    app_version: str = "0.1.0"
    environment: str = "development"
    
    # OpenAI API key
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    # ---------------------------------------------------------
    # Embeddings
    # ---------------------------------------------------------

    # Embedding provider can be "local" or "openai"
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    # Local embedding settings
    local_embedding_model: str = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # OpenAI Embedding model
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    openai_embedding_dimensions: int | None = optional_int_from_env("OPENAI_EMBEDDING_DIMENSIONS")
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", 64))
    
    # ---------------------------------------------------------
    # Explanation
    # ---------------------------------------------------------
    # Explanation provider can be "template" or "openai"
    explanation_provider: str = os.getenv("EXPLANATION_PROVIDER", "template")
    openai_explanation_model: str = os.getenv(
        "OPENAI_EXPLANATION_MODEL", 
        "gpt-5.4-mini"
    )

    # TMDB API settings
    tmdb_api_read_access_token: str | None = os.getenv("TMDB_API_READ_ACCESS_TOKEN")
    tmdb_language: str = os.getenv("TMDB_LANGUAGE", "en-US")
    tmdb_max_movies: int = int(os.getenv("TMDB_MAX_MOVIES", 20000))
    tmdb_min_vote_count: int = int(os.getenv("TMDB_MIN_VOTE_COUNT", 50))
    tmdb_min_popularity: float = float(os.getenv("TMDB_MIN_POPULARITY", 2.0))
    tmdb_request_sleep_seconds: float = float(os.getenv("TMDB_REQUEST_SLEEP_SECONDS", 0.05))


    # Intent parsing settings
    intent_parser_provider: str = os.getenv("INTENT_PARSER_PROVIDER", "template")
    openai_intent_model: str = os.getenv("OPENAI_INTENT_MODEL", "gpt-5.4-mini")


    # Data paths
    backend_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = backend_dir / "data"
    processed_data_dir: Path = data_dir / "processed"
    movie_documents_path: Path = processed_data_dir / "movie_documents.jsonl"

    # Chroma vector DB path
    chroma_db_dir: Path = backend_dir / "chroma_db"
    chroma_collection_prefix: str = os.getenv(
        "CHROMA_COLLECTION_PREFIX",
        "movie-docs",
    )
    chroma_collection_name: str | None = os.getenv("CHROMA_COLLECTION_NAME") or None

    # Ingestion settings
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", 32))

    # SQLite database path
    sqlite_db_path: Path = backend_dir / "movie_agent.db"
    database_url: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{sqlite_db_path}"
    )

    # ---------------------------------------------------------
    # Bounded LLM reranker
    # ---------------------------------------------------------
    llm_reranker_provider: str = os.getenv("LLM_RERANKER_PROVIDER", "disabled")
    openai_reranker_model: str = os.getenv("OPENAI_RERANKER_MODEL", "gpt-5.4-mini")
    llm_reranker_shortlist_size: int = int(os.getenv("LLM_RERANKER_SHORTLIST_SIZE", 15))
    llm_reranker_max_overview_chars: int = int(os.getenv("LLM_RERANKER_MAX_OVERVIEW_CHARS", 500))


settings = Settings()