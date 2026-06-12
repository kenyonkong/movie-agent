from app.services.intent_parser import IntentParserService


def print_intent(query: str, use_llm_intent: bool) -> None:
    parser = IntentParserService()

    intent = parser.parse_intent(
        query=query,
        use_llm_intent=use_llm_intent,
    )

    print("\n" + "=" * 80)
    print(f"Provider: {parser.get_provider_name(use_llm_intent)}")
    print(f"Raw query: {query}")
    print(intent.model_dump_json(indent=2))


def main() -> None:
    queries = [
        "I want something like Her or After Yang, quiet and futuristic, but not too slow.",
        "A dark psychological thriller with obsession and mystery, but not supernatural horror.",
        "A warm funny family adventure that is not too childish.",
    ]

    for query in queries:
        print_intent(query=query, use_llm_intent=False)

    print("\nNow testing LLM intent parsing if configured...\n")

    for query in queries[:2]:
        print_intent(query=query, use_llm_intent=True)


if __name__ == "__main__":
    main()