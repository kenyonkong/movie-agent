import argparse

from openai import OpenAI
from sqlalchemy.dialects.sqlite import insert

from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.db.models import TasteProfileSnapshot
from app.services.movie_catalog import MovieCatalogService
from app.services.taste_profile import build_profile, oldest_reviews


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a taste profile from the oldest 50 reviews.")
    parser.add_argument("--user-id", default="demo_user")
    parser.add_argument("--model", default=settings.openai_explanation_model)
    args = parser.parse_args()
    with SessionLocal() as db:
        reviews = oldest_reviews(db, args.user_id, MovieCatalogService())
    print(f"Analyzing {len(reviews)} reviews, {reviews[0].reviewed_on} to {reviews[-1].reviewed_on}.",
          flush=True)
    with OpenAI(api_key=settings.openai_api_key, timeout=180) as client:
        profile = build_profile(client, args.model, reviews)
    # Publish only after both model passes and all provenance checks succeed.
    table = TasteProfileSnapshot.__table__
    table.create(engine, checkfirst=True)
    write = insert(table).values(user_id=args.user_id, document=profile.model_dump(mode="json"))
    with engine.begin() as connection:
        connection.execute(write.on_conflict_do_update(
            index_elements=[table.c.user_id], set_={"document": write.excluded.document},
        ))
    print(f"Saved {len(profile.preferences)} preferences grounded in {len(profile.evidence)} observations.")


if __name__ == "__main__":
    main()
