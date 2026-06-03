from sqlalchemy import desc, select

from app.db.database import SessionLocal
from app.db.models import UserFeedback
from app.services.memory_service import MemoryService

def main() -> None:
    db = SessionLocal()
    memory_service = MemoryService()

    try:
        statement = (
            select(UserFeedback)
            .order_by(desc(UserFeedback.created_at))
            .limit(20)
        )

        feedback_items = db.execute(statement).scalars().all()

        print("\n========== RECENT FEEDBACK ==========")

        if not feedback_items:
            print("No feedback found yet.")
        else:
            for item in feedback_items:
                print(
                    f"[{item.created_at}] "
                    f"user={item.user_id} "
                    f"movie={item.title} "
                    f"action={item.action} "
                    f"genres={item.genres}"
                )

        print("\n========== DEMO USER MEMORY SUMMARY ==========")
        summary = memory_service.get_memory_summary(db=db, user_id="demo_user")
        print(summary.model_dump())

    finally:
        db.close()


if __name__ == "__main__":
    main()