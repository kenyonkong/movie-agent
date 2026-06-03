from app.db.database import create_db_tables
from app.core.config import settings

def main() -> None:
    create_db_tables()

    print("Database initialized successfully.")
    print(f"Database URL: {settings.database_url}")
    print(f"SQLite path: {settings.sqlite_db_path}")

if __name__ == "__main__":
    main()