from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes import reviews as review_route, taste_profile as route
from app.db.database import Base, get_db
from app.db.models import DoubanReviewSource, MovieReview, TasteProfileSnapshot
from app.services import taste_history as history
from app.services import taste_profile as taste
from app.services.movie_catalog import MovieCatalogService


@pytest.fixture
def cohort(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    start = datetime(2020, 1, 1)
    with Session(engine) as db:
        for key in range(1, 84):
            db.add(MovieReview(id=key, movie_id=str(key), title=f"Movie {key}", rating=8,
                user_id="other" if key == 83 else "demo_user",
                body="星期六看的。" if key == 82 else f"Review {key}",
                updated_at=start + timedelta(days=key)))
        for key in (81, 82):
            db.add(DoubanReviewSource(review_id=key, record_id=str(key), marked_at=start,
                original_body="星期六看的。" if key == 82 else "Before editing",
                english_body="Watched on Saturday."))
        db.commit()
        yield engine, taste.ordered_reviews(db, "demo_user", MovieCatalogService(tmp_path / "missing.csv"))
    engine.dispose()


@pytest.mark.parametrize("total, ends", [(0, []), (7, [7]), (50, [50]), (51, [50, 51]),
                                         (80, [50, 80]), (387, [*range(50, 381, 30), 387])])
def test_period_boundaries(total, ends):
    assert history.period_ends(total) == ends


def test_incremental_history_and_original_evidence(cohort, monkeypatch):
    engine, inputs = cohort
    assert [r.review_id for r in inputs] == [81, 82, *range(1, 81)]
    assert inputs[1].display_body == "Watched on Saturday."
    analyzed, summarized = [], []

    def respond(client, model, prompt, payload, schema):
        if schema is history.AnalysisBatch:
            analyzed.extend(r["review_id"] for r in payload)
            return schema(reviews=[dict(review_id=r["review_id"], observations=[] if r["review_id"] == 82 else [
                dict(quote=r["body"], interpretation="Likes their presence.", aspect="presence", exception=False)
            ]) for r in payload])
        assert schema is history.Summary
        summarized.append([r["review_id"] for r in payload])
        return schema(findings=[dict(sentence="You enjoy screen presence.",
            supporting=[payload[0]["id"], payload[-1]["id"]])])

    monkeypatch.setattr(history, "ask", respond)
    def build(rows, previous=None):
        observations = history.observations_for(engine, None, "test", "demo_user", rows, previous)
        return history.build_history(None, "test", rows, observations, previous)

    initial = build(inputs[:81])
    assert [p.through for p in initial.history] == [50, 80, 81]
    assert [len(set(s)) for s in summarized] == [49, 79, 80]
    assert set(summarized[0]) == {r.review_id for r in inputs[:50]} - {82}
    assert len(analyzed) == 81
    analyzed.clear()
    summarized.clear()
    current = build(inputs, initial)
    assert analyzed == [80]
    assert len(summarized) == 1
    assert current.history[:2] == initial.history[:2]
    assert current.history[-1].partial and current.history[-1].through == 82
    assert current.reviews[1].original_body == "星期六看的。"
    assert current.aspects[0].key == "presence"
    assert len(current.preferences[0].supporting) == 81

    app = FastAPI()
    app.include_router(route.router)
    app.include_router(review_route.router)
    refreshed = []
    monkeypatch.setattr(review_route, "refresh_after_save", lambda bind, user, model: refreshed.append((user, model)))
    monkeypatch.setattr(review_route.movie_catalog, "get_movies_by_id", lambda ids: {})
    def test_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = test_db
    with Session(engine) as db:
        db.add(TasteProfileSnapshot(user_id="demo_user", document=current.model_dump(mode="json")))
        db.commit()
    with TestClient(app) as client:
        assert client.get("/users/demo_user/taste-profile").json() == current.model_dump(mode="json")
        assert client.get("/users/other/taste-profile").json() is None
        assert client.put("/users/demo_user/reviews/1", json=dict(title="Movie 1", rating=4, body="Edited")).is_success
        assert refreshed == [("demo_user", "test")]
        assert client.get("/users/demo_user/taste-profile").json()["is_current"] is False
        with Session(engine) as db:
            db.get(MovieReview, 81).body = "Edited."
            db.commit()
        assert client.get("/users/demo_user/taste-profile").json()["is_current"] is False
    analyzed.clear()
    summarized.clear()
    edited = [inputs[0].model_copy(update={"body": "Edited.", "display_body": "Edited."}), *inputs[1:]]
    rebuilt = build(edited, current)
    assert analyzed == [81] and len(summarized) == 3
    assert rebuilt.history[0].digest != current.history[0].digest


def test_legacy_snapshot_reuses_original_observations(cohort, monkeypatch):
    engine, inputs = cohort
    review = inputs[1]
    e = taste.Evidence(review_id=review.review_id, evidence_id=7, quote=review.body, interpretation="Original note")
    old = taste.TasteProfile(reviews=[taste.SourceReview(**review.model_dump(exclude={"body"}))],
        evidence=[e], preferences=[], model="test", generated_at=datetime.now(timezone.utc))
    with Session(engine) as db:
        db.add(TasteProfileSnapshot(user_id="demo_user", document=old.model_dump(mode="json")))
        db.commit()
        previous = taste.saved_profile(db, "demo_user")
        assert previous.reviews[0].original_body == review.body

    def tag(client, model, prompt, payload, schema):
        assert schema is history.TagBatch and payload[0]["evidence_id"] == 7
        return schema(tags=[dict(evidence_id=7, aspect="other", exception=False)])
    monkeypatch.setattr(history, "ask", tag)
    result = history.observations_for(engine, None, "test", "demo_user", [review], previous)
    assert result[review.review_id][0].interpretation == "Original note"


@pytest.mark.parametrize("fault", ["missing", "quote"])
def test_rejects_invalid_extraction(cohort, monkeypatch, fault):
    _, inputs = cohort
    rows = [] if fault == "missing" else [dict(review_id=81, observations=[
        dict(quote="invented", interpretation="acting", aspect="other", exception=False)])]
    monkeypatch.setattr(history, "ask", lambda *args: history.AnalysisBatch(reviews=rows))
    with pytest.raises(ValueError):
        history.analyze_batch(None, "test", inputs[:1], None)


def test_summary_rejects_unknown_and_single_film_citations(monkeypatch):
    evidence = [taste.Evidence(evidence_id=i, review_id=review, quote="quote", interpretation="note")
                for i, review in [(1, 10), (2, 10), (3, 11)]]
    draft = history.Summary(findings=[taste.Finding(sentence="Claim", supporting=ids)
                                      for ids in [[1, 99], [1, 2], [1, 1], [1, 3]]])
    monkeypatch.setattr(history, "ask", lambda *args: draft)
    assert history.summarize(None, "test", evidence, {11}) == draft.findings[-1:]
