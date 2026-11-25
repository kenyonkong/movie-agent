from contextlib import closing
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes import feedback, reviews
from app.db.database import Base, get_db
from app.db.models import MovieReview
from app.services.movie_catalog import MovieCatalogService
from app.scripts.import_douban_reviews import PreparedExport, import_reviews


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'reviews.db').as_posix()}")
    Base.metadata.create_all(engine)
    catalog = tmp_path / "movies.csv"
    catalog.write_text("id,title,poster_path\n1,Spider-Man,/spider.jpg\n", encoding="utf-8")
    monkeypatch.setattr(reviews, "movie_catalog", MovieCatalogService(catalog))
    app = FastAPI()
    app.include_router(reviews.router)
    app.include_router(feedback.router)

    def test_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def test_reviews_persist_and_edits_move_to_top(client):
    path = "/users/demo_user/reviews"
    assert client.get(path).json() == []
    first = {"title": "Spider-Man", "rating": 4, "body": "A great rewatch."}
    second = {"title": "Her", "rating": 1, "body": "Worth a look."}

    created = client.put(f"{path}/1", json=first)
    assert created.status_code == 200
    assert created.json()["rating"] == 4
    assert created.json()["watched"] is True
    assert created.json()["poster_url"] == "https://image.tmdb.org/t/p/w500/spider.jpg"
    assert datetime.fromisoformat(created.json()["updated_at"]).utcoffset() is not None
    assert client.put(f"{path}/2", json=second).status_code == 200
    assert [review["movie_id"] for review in client.get(path).json()] == ["2", "1"]

    changed = {**first, "rating": 5, "body": "Even better the second time."}
    edited = client.put(f"{path}/1", json=changed)
    assert edited.status_code == 200
    saved = client.get(path).json()
    assert [review["movie_id"] for review in saved] == ["1", "2"]
    assert saved[0]["rating"] == 5
    assert saved[0]["body"] == changed["body"]
    assert saved[0]["poster_url"] == created.json()["poster_url"]
    assert saved[1]["poster_url"] is None
    assert client.get("/users/another_user/reviews").json() == []


def test_review_marks_watched_and_preserves_existing_feedback(client):
    feedback = {"movie_id": "1", "title": "Spider-Man", "genres": "Action", "action": "like"}
    assert client.post("/feedback/", json=feedback).status_code == 200
    assert client.post("/feedback/", json={**feedback, "action": "save"}).status_code == 200
    response = client.put(
        "/users/demo_user/reviews/1",
        json={"title": "Spider-Man", "rating": 4, "body": "Fun."},
    )
    assert response.status_code == 200
    states = client.get("/feedback/demo_user").json()
    assert len(states) == 1
    assert states[0]["watched"] is True
    assert states[0]["saved"] is True
    assert states[0]["preference"] == "like"
    assert states[0]["genres"] == "Action"


@pytest.mark.parametrize(
    "changes",
    [{"rating": None}, {"rating": 0}, {"rating": 6}, {"rating": 3.5}, {"body": "  "}],
)
def test_review_requires_valid_rating_and_text(client, changes):
    payload = {"title": "Her", "rating": 4, "body": "A great rewatch.", **changes}
    response = client.put("/users/demo_user/reviews/1", json=payload)
    assert response.status_code == 422


def test_legacy_half_star_rating_rounds_up(client):
    test_db = client.app.dependency_overrides[get_db]
    with closing(test_db()) as sessions:
        db = next(sessions)
        db.add(MovieReview(
            user_id="demo_user",
            movie_id="1",
            title="Spider-Man",
            rating=7,
            body="A legacy review.",
            updated_at=datetime.now(timezone.utc),
        ))
        db.commit()

    response = client.get("/users/demo_user/reviews")
    assert response.status_code == 200
    assert response.json()[0]["rating"] == 4


def test_import_keeps_douban_dates_and_is_repeatable(client):
    source = PreparedExport.model_validate({
        "source": "douban",
        "records": [
            {
                "record_id": str(movie_id),
                "movie_id": str(movie_id),
                "match_status": "matched",
                "title": f"Film {movie_id}",
                "rating": 4,
                "review_original": "好看",
                "review_en": "A good watch.",
                "marked_date": marked_date,
            }
            for movie_id, marked_date in [(1, "2023-07-21"), (2, "2018-01-01")]
        ],
    })
    test_db = client.app.dependency_overrides[get_db]
    with closing(test_db()) as sessions:
        db = next(sessions)
        with db.begin():
            assert import_reviews(db, source, "demo_user")["imported"] == 2
        with db.begin():
            assert import_reviews(db, source, "demo_user")["existing"] == 2

    path = "/users/demo_user/reviews"
    edited = client.put(f"{path}/2", json={"title": "Film 2", "rating": 5, "body": "Edited."})
    assert edited.json()["marked_date"] == "2018-01-01"
    assert edited.json()["review_en"] is None
    saved = client.get(path).json()
    assert [review["movie_id"] for review in saved] == ["1", "2"]
    assert saved[0]["marked_date"] == "2023-07-21"
    assert saved[0]["title"] == "Spider-Man"
    assert saved[0]["review_en"] == "A good watch."
    assert all(review["watched"] for review in saved)
