import pytest

from app.services.intent_parser import IntentParserService


@pytest.mark.parametrize(
    ("query", "language_code"),
    [
        ("English-language movies only", "en"),
        ("Show me a movie in Korean", "ko"),
        ("A French language romance", "fr"),
        ("Japanese-language animation", "ja"),
        ("Movies in Spanish", "es"),
        ("A Chinese language drama", "zh"),
    ],
)
def test_template_parser_extracts_language_constraints(
    query: str,
    language_code: str,
) -> None:
    intent = IntentParserService(
        provider="template"
    ).parse_intent(
        query=query,
        use_llm_intent=False,
    )

    assert intent.hard_constraints.allowed_languages == [
        language_code
    ]


def test_template_parser_preserves_precise_numeric_boundaries() -> None:
    intent = IntentParserService(
        provider="template"
    ).parse_intent(
        query="A Korean-language movie under 120 minutes after 2010",
        use_llm_intent=False,
    )

    constraints = intent.hard_constraints
    assert constraints.allowed_languages == ["ko"]
    assert constraints.max_runtime == 119
    assert constraints.min_release_year == 2011
