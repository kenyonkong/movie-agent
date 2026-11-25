from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes import taste_profile as route
from app.db.database import Base, get_db
from app.db.models import DoubanReviewSource, MovieReview, TasteProfileSnapshot
from app.services import taste_profile as taste
from app.services.movie_catalog import MovieCatalogService


@pytest.fixture
def cohort(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    catalog = MovieCatalogService(tmp_path / "missing-catalog.csv")
    start = datetime(2020, 1, 1)
    with Session(engine) as db:
        for key in range(1, 53):
            db.add(MovieReview(
                id=key, movie_id=str(key), title=f"Movie {key}", rating=8,
                user_id="other" if key == 52 else "demo_user",
                body="星期六看的。" if key == 51 else f"Current review {key}",
                updated_at=start + timedelta(days=key),
            ))
        for key in (50, 51):
            db.add(DoubanReviewSource(
                review_id=key, record_id=str(key), marked_at=start, english_body="Watched on Saturday.",
                original_body="星期六看的。" if key == 51 else "Before edit",
            ))
        db.commit()
        with pytest.raises(ValueError, match="Found 1"):
            taste.oldest_reviews(db, "other", catalog)
        yield engine, taste.oldest_reviews(db, "demo_user", catalog)
    engine.dispose()


def test_full_cohort_synthesized_once_and_served_from_sqlite(cohort, monkeypatch):
    engine, inputs = cohort
    assert [r.review_id for r in inputs] == [50, 51, *range(1, 49)]
    assert inputs[0].display_body == "Current review 50"
    assert inputs[1].display_body == "Watched on Saturday."
    synthesis_calls = []

    def respond(client, model, prompt, payload, schema):
        if schema is taste.Extraction:
            assert all(set(row) == {"review_id", "body"} for row in payload)
            return taste.Extraction(reviews=[
                taste.ReviewAnalysis(review_id=row["review_id"], observations=[
                    taste.Observation(quote=row["body"], interpretation="The reviewer enjoyed the acting.")
                ] if row["review_id"] != 51 else []) for row in payload
            ])
        synthesis_calls.append(payload)
        return taste.Synthesis(preferences=[
            taste.Preference(theme="Acting", claim="You enjoy expressive acting.",
                             supporting=[1, 2], exceptions=[3])
        ])

    monkeypatch.setattr(taste, "ask", respond)
    profile = taste.build_profile(None, "test-model", inputs)
    assert profile.reviews[1].original_body == "星期六看的。"
    assert len(synthesis_calls) == 1
    assert [r["review_id"] for r in synthesis_calls[0]] == [r.review_id for r in inputs]
    assert synthesis_calls[0][1]["observations"] == []
    assert len(profile.evidence) == 49

    app = FastAPI()
    app.include_router(route.router)

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    with Session(engine) as db:
        db.add(TasteProfileSnapshot(user_id="demo_user", document=profile.model_dump(mode="json")))
        db.commit()
    with TestClient(app) as client:
        assert client.get("/users/other/taste-profile").json() is None
        assert client.get("/users/demo_user/taste-profile").json() == profile.model_dump(mode="json")
        # The existing profile predates original_body. Recover its original Douban text
        # even after an edit, without assigning the new text to old evidence.
        legacy = profile.model_dump(mode="json")
        for review in legacy["reviews"]:
            del review["original_body"]
        with Session(engine) as db:
            db.get(MovieReview, 51).body = "Edited after profiling."
            db.get(TasteProfileSnapshot, "demo_user").document = legacy
            db.commit()
        restored = client.get("/users/demo_user/taste-profile").json()
        assert restored == profile.model_dump(mode="json")


@pytest.mark.parametrize("fault", ["missing review", "invented quote"])
def test_rejects_incomplete_or_ungrounded_extraction(cohort, monkeypatch, fault):
    _, inputs = cohort
    rows = [] if fault == "missing review" else [
        taste.ReviewAnalysis(review_id=inputs[0].review_id, observations=[
            taste.Observation(quote="I never said this", interpretation="Acting")
        ])
    ]
    monkeypatch.setattr(taste, "ask", lambda *args: taste.Extraction(reviews=rows))
    with pytest.raises(ValueError):
        taste.extract_batch(None, "test", inputs[:1])


@pytest.mark.parametrize("support,exceptions", [([1, 2], []), ([1, 3], [3]), ([1, 4], [])])
def test_rejects_unsupported_synthesis(support, exceptions):
    evidence = [taste.Evidence(evidence_id=key, review_id=review_id, quote="quote", interpretation="note")
                for key, review_id in [(1, 10), (2, 10), (3, 11)]]
    claim = taste.Preference(theme="Theme", claim="Claim", supporting=support, exceptions=exceptions)
    assert taste.citation_error(claim, {item.evidence_id: item.review_id for item in evidence})


def test_synthesis_repairs_a_bad_reference_using_the_same_evidence(cohort, monkeypatch):
    _, inputs = cohort
    evidence = [
        taste.Evidence(evidence_id=i, review_id=row.review_id, quote=row.body, interpretation="Acting")
        for i, row in enumerate(inputs[:2], start=1)
    ]
    attempts = []

    def respond(client, model, prompt, payload, schema):
        attempts.append(payload)
        supporting = [1, 99] if len(attempts) == 1 else [1, 2]
        return taste.Synthesis(preferences=[
            taste.Preference(theme="Acting", claim="You value acting.", supporting=supporting, exceptions=[]),
            taste.Preference(theme="Cast", claim="Unsupported claim", supporting=[99], exceptions=[]),
        ])

    monkeypatch.setattr(taste, "ask", respond)
    result = taste.synthesize(None, "test", inputs, evidence)
    assert attempts[1][:-1] == attempts[0]
    assert "99" in attempts[1][-1]["validation_error"]
    assert [p.supporting for p in result.preferences] == [[1, 2]]
