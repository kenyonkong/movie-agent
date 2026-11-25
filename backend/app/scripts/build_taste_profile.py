import argparse

from app.core.config import settings
from app.db.database import engine
from app.services.taste_history import refresh_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Build taste milestones and a current profile from all reviews.")
    parser.add_argument("--user-id", default="demo_user")
    parser.add_argument("--model", default=settings.openai_explanation_model)
    args = parser.parse_args()
    profile = refresh_profile(engine, args.user_id, args.model)
    print(f"Saved {len(profile.history)} periods through {len(profile.reviews)} reviews, "
          f"with {len(profile.evidence)} observations.")


if __name__ == "__main__":
    main()
