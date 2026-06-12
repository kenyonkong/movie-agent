import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv() # Load environment variables from .env file


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Movie Agent API")
    app_version: str = "0.1.0"
    environment: str = "development"

    # Embedding provider can be "local" or "openai"
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")

    # Explanation provider can be "template" or "openai"
    explanation_provider: str = os.getenv("EXPLANATION_PROVIDER", "template")

    # OpenAI settings
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    openai_explanation_model: str = os.getenv(
        "OPENAI_EXPLANATION_MODEL", 
        "gpt-5.4-mini"
    )

    # Intent parsing settings
    intent_parser_provider: str = os.getenv("INTENT_PARSER_PROVIDER", "template")
    openai_intent_model: str = os.getenv("OPENAI_INTENT_MODEL", "gpt-5.4-mini")

    # Local embedding settings
    local_embedding_model : str = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Data paths
    backend_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = backend_dir / "data"
    processed_data_dir: Path = data_dir / "processed"
    movie_documents_path: Path = processed_data_dir / "movies_documents.jsonl"

    # Chroma vector DB path
    chroma_db_dir: Path = backend_dir / "chroma_db"
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "movie_documents")

    # Ingestion settings
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", 32))

    # SQLite database path
    sqlite_db_path: Path = backend_dir / "movie_agent.db"
    database_url: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{sqlite_db_path}"
    )

settings = Settings()