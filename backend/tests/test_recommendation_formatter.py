from app.services.recommendation_formatter import RecommendationFormatter


def test_format_one_includes_runtime() -> None:
    recommendation = RecommendationFormatter().format_one(
        candidate={
            "id": "1",
            "title": "Movie One",
            "runtime": 110,
        },
        explanation="A test explanation.",
    )

    assert recommendation.runtime == 110
