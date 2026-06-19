from openai import OpenAI

from app.core.config import settings


def main() -> None:
    print(f"Testing {settings.app_name}")
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to backend/.env first."
        )

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model=settings.openai_explanation_model,
        input="Write one short sentence explaining why Her is a quiet emotional sci-fi romance.",
        temperature=0.3,
    )

    print(response.output_text)


if __name__ == "__main__":
    main()