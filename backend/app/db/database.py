from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Every database table model will inherit from this class.
    """
    pass

# Create the SQLAlchemy engine using the database URL from settings
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False} # Required for SQLite to allow multiple threads
    if settings.database_url.startswith("sqlite") 
    else {}
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def create_db_tables() -> None:
    """
    Create the database tables based on the defined ORM models.
    This should be called at application startup to ensure the database schema is set up.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session.

    This can be used in FastAPI endpoints to access the database.
    It ensures that the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()