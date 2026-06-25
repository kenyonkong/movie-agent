import json
import re

from openai import OpenAI

from app.core.config import settings
from app.db.schemas import MovieIntent, MovieHardConstraints

class IntentParserService:
    """
    Parses raw natural-language movie queries into structured movie intent.

    Design principle:
    The intent parser does not recommend movies.
    It only extracts user intent and creates a better retrieval query.
    """

    def __init__(
        self, 
        provider: str | None = None, 
        model: str | None = None,            
    ) -> None:
        self.provider = (
            provider or settings.intent_parser_provider
        ).strip().lower()

        self.model = (
            model or settings.openai_intent_model
        )

        self.client: OpenAI | None = None

        # if self.provider == "openai":
            # if not settings.openai_api_key:
            #     raise ValueError("OpenAI API key is required for the OpenAI intent parser.")
            
            # self.client = OpenAI(api_key=settings.openai_api_key)
        
    
    def _get_client(self) -> OpenAI:
        if self.client is not None:
            return self.client

        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for OpenAI intent parsing."
            )

        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

        return self.client


    def get_provider_name(self, use_llm_intent: bool) -> str:
        if use_llm_intent and self.provider == "openai":
            return f"OpenAI: ({self.model})"
        return "template"
    

    def parse_intent(
        self,
        query: str, 
        use_llm_intent: bool
    ) -> MovieIntent:
        """
        Parse the user's raw query into structured intent.

        Falls back to a deterministic template parser if:
        - use_llm_intent is false
        - provider is not openai
        - OpenAI parsing fails
        """
        if not use_llm_intent or self.provider != "openai":
            # Fallback to template-based parsing
            return self._parse_with_template(query)

        try:
            # Use OpenAI to parse the intent
            return self._parse_with_openai(query)
        except Exception as error:
            # If OpenAI parsing fails, fall back to template-based parsing
            print(
                "Failed to parse intent with OpenAI; "
                f"using template parser instead: {error}"
            )
            return self._parse_with_template(query)
    

    def _parse_with_template(
        self,
        query: str,
    ) -> MovieIntent:
        cleaned_query = re.sub(
            r"\s+",
            " ",
            query,
        ).strip()

        lower_query = cleaned_query.lower()

        avoid: list[str] = []
        readable_constraints: list[str] = []

        hard = MovieHardConstraints()

        if "not too slow" in lower_query:
            avoid.append("too slow")

        if "not too depressing" in lower_query:
            avoid.append("too depressing")

        if "not too scary" in lower_query:
            avoid.append("too scary")

        # "under 150 minutes" means strictly below 150.
        under_minutes_match = re.search(
            r"\bunder\s+(\d+)\s+minutes?\b",
            lower_query,
        )

        if under_minutes_match:
            boundary = int(
                under_minutes_match.group(1)
            )

            hard.max_runtime = boundary - 1

            readable_constraints.append(
                f"Runtime under {boundary} minutes"
            )

        at_most_minutes_match = re.search(
            r"\bat most\s+(\d+)\s+minutes?\b",
            lower_query,
        )

        if at_most_minutes_match:
            boundary = int(
                at_most_minutes_match.group(1)
            )

            hard.max_runtime = boundary

            readable_constraints.append(
                f"Runtime at most {boundary} minutes"
            )

        if "under two hours" in lower_query:
            hard.max_runtime = 119
            readable_constraints.append(
                "Runtime under two hours"
            )

        if "at most two hours" in lower_query:
            hard.max_runtime = 120
            readable_constraints.append(
                "Runtime at most two hours"
            )

        before_year_match = re.search(
            r"\bbefore\s+((?:18|19|20)\d{2})\b",
            lower_query,
        )

        if before_year_match:
            boundary = int(
                before_year_match.group(1)
            )

            hard.max_release_year = boundary - 1

            readable_constraints.append(
                f"Released before {boundary}"
            )

        after_year_match = re.search(
            r"\bafter\s+((?:18|19|20)\d{2})\b",
            lower_query,
        )

        if after_year_match:
            boundary = int(
                after_year_match.group(1)
            )

            hard.min_release_year = boundary + 1

            readable_constraints.append(
                f"Released after {boundary}"
            )

        language_phrases = {
            r"\b(?:english-language|english language|movies? in english)\b": "en",
            r"\b(?:korean-language|korean language|movies? in korean)\b": "ko",
            r"\b(?:french-language|french language|movies? in french)\b": "fr",
            r"\b(?:japanese-language|japanese language|movies? in japanese)\b": "ja",
            r"\b(?:spanish-language|spanish language|movies? in spanish)\b": "es",
            r"\b(?:chinese-language|chinese language|movies? in chinese)\b": "zh",
        }

        for phrase, language_code in (
            language_phrases.items()
        ):
            if phrase in lower_query:
                hard.allowed_languages.append(
                    language_code
                )

                readable_constraints.append(
                    f"Original language: {language_code}"
                )

        return MovieIntent(
            raw_query=query,
            query_rewrite=cleaned_query,
            reference_movies=[],
            moods=[],
            themes=[],
            genres=[],
            pacing=None,
            tone=[],
            avoid=avoid,
            constraints=readable_constraints,
            hard_constraints=hard,
            confidence=0.1,
            parser_notes=(
                "Conservative template parser used. "
                "Only obvious numeric and language constraints were extracted."
            ),
        )


    def _parse_with_openai(self, query: str) -> MovieIntent:
        """
        Parse intent using OpenAI Structured Outputs.
        """
        # if self.client is None:
        #     raise ValueError("OpenAI client is not initialized.")

        client = self._get_client()

        response = client.responses.parse(
            model=self.model,
            instructions=self._system_prompt(),
            input=query,
            text_format=MovieIntent
        )
        
        parsed_intent = response.output_parsed
        if parsed_intent is None:
            raise ValueError(
                "OpenAI returned no parsed MovieIntent."
            )

        # The application, not the model, is authoritative for raw_query.
        return parsed_intent.model_copy(
            update={
                "raw_query": query,
            }
        )



    def _system_prompt(self) -> str:
        return """
You are an intent parser for a movie recommendation system.

Your job is to convert a user's natural-language request into a
structured MovieIntent object.

You do not recommend movies.

Separate soft preferences from hard constraints.

A hard constraint is an explicit requirement that every returned movie
must satisfy. Examples include:

- "Only Christopher Nolan movies."
- "It must star Leonardo DiCaprio."
- "Under 150 minutes."
- "At most two hours."
- "Released before 2010."
- "Korean-language movies only."
- "No horror."
- "Rated at least 7."

Do not convert vague preferences into hard constraints.

Examples:

- "Something like Christopher Nolan" is not a director constraint.
- "Prefer something short" is not a maximum runtime.
- "Maybe Korean" is not a language constraint.
- "Not too slow" is a soft pacing preference, not a numeric runtime rule.

Interpret numeric boundaries precisely:

- "under 150 minutes" means max_runtime = 149
- "at most 150 minutes" means max_runtime = 150
- "over 120 minutes" means min_runtime = 121
- "at least 120 minutes" means min_runtime = 120
- "before 2010" means max_release_year = 2009
- "after 2000" means min_release_year = 2001
- "from 2000 onward" means min_release_year = 2000
- "around 120 minutes" means min_runtime = 105 and max_runtime = 135
- For approximate runtime requests using words like "around", "about", or "roughly" followed by a number, use a tolerance of ±15 minutes unless the user gives a more specific range.

Language fields should use ISO-style TMDB language codes when known:

- English → en
- Korean → ko
- French → fr
- Japanese → ja
- Spanish → es
- Chinese → zh

Rules:

1. Do not recommend movies.
2. Do not invent movie facts.
3. Preserve explicitly mentioned reference movies.
4. Put vague mood, tone, pacing, theme, and style preferences in the
   normal intent fields.
5. Put only enforceable requirements in hard_constraints.
6. Create a concise, information-rich query_rewrite for semantic search.
7. Preserve hard requirements in the query rewrite as retrieval hints,
   even though they will also be enforced deterministically.
8. Return empty arrays or null values when a constraint is absent.
""".strip()