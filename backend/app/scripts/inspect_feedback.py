from sqlalchemy import desc, select

from app.db.database import SessionLocal
from app.db.models import UserMoviePreference
from app.services.memory_service import MemoryService


def main() -> None:
    db = SessionLocal()
    memory_service = MemoryService()

    try:
        statement = (
            select(UserMoviePreference)
            .order_by(desc(UserMoviePreference.updated_at))
            .limit(20)
        )

        preference_items = db.execute(statement).scalars().all()

        print("\n========== RECENT USER MOVIE PREFERENCES ==========")

        if not preference_items:
            print("No preferences found yet.")
        else:
            for item in preference_items:
                print(
                    f"[updated_at={item.updated_at}] "
                    f"user={item.user_id} "
                    f"movie={item.title} "
                    f"preference={item.preference} "
                    f"watched={item.watched} "
                    f"saved={item.saved} "
                    f"genres={item.genres}"
                )

        print("\n========== DEMO USER MEMORY SUMMARY ==========")
        summary = memory_service.get_memory_summary(db=db, user_id="demo_user")
        print(summary.model_dump())

    finally:
        db.close()


if __name__ == "__main__":
    main()