import json
import re

from openai import OpenAI

from app.core.config import settings
from app.db.schemas import MovieIntent

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
    
    def _parse_with_template(self, query: str) -> MovieIntent:
        """
        Lightweight fallback parser.

        This does not try to be smart. It preserves the raw query and extracts
        a few obvious constraints using simple keyword rules.
        """
        cleaned_query = re.sub(r"\s+", " ", query).strip()

        # lower_query = cleaned_query.lower()
        # avoid = []
        # if "not too slow" in lower_query:
        #     avoid.append("too slow")

        # if "not too depressing" in lower_query:
        #     avoid.append("too depressing")

        # if "not too scary" in lower_query:
        #     avoid.append("too scary")

        # if "not too violent" in lower_query:
        #     avoid.append("too violent")

        return MovieIntent(
            raw_query=query,
            query_rewrite=cleaned_query,
            reference_movies=[], 
            moods=[], 
            themes=[],
            genres=[],
            pacing=None, 
            tone=[], 
            avoid=[], 
            constraints=[],
            confidence=0.3,
            parser_notes="Template parser used. Query rewrite is mostly the original query.",
        )


    def _parse_with_openai(self, query: str) -> MovieIntent:
        """
        Parse intent using OpenAI Structured Outputs.
        """
        # if self.client is None:
        #     raise ValueError("OpenAI client is not initialized.")

        schema = self._intent_json_schema()

        client = self._get_client()
        response = client.responses.create(
            model=self.model, 
            input=[
                {"role":"system",
                "content":self._system_prompt(), 
                }, 
                {"role":"user", 
                "content":query,
                },
            ],
            text={
                "format": {
                    "type": "json_schema", 
                    "name": "Movie_intent",
                    "schema": schema,
                    "strict": True,
                }
            }, 
            temperature=0.2, 
        )

        parsed = json.loads(response.output_text)
        return MovieIntent(**parsed)


    def _system_prompt(self) -> str:
            return """
    You are an intent parser for a movie recommendation system.

    Your job is to convert a user's raw natural-language request into structured intent.

    Important rules:
    - Do not recommend movies.
    - Do not invent facts about movies.
    - Extract only what the user asked for.
    - If the user gives a reference movie, include it in reference_movies.
    - If the user says what to avoid, include it in avoid.
    - Create a query_rewrite optimized for semantic vector search.
    - The query_rewrite should be concise but information-rich.
    - The query_rewrite should preserve the user's main intent.
    - Do not include movies in query_rewrite unless they help retrieval.
    """.strip()


    def _intent_json_schema(self) -> dict:
        """
        JSON Schema used for OpenAI Structured Outputs.

        We require every field so the returned object is predictable.
        Fields that do not apply should be empty arrays, null, or empty strings.
        """
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "raw_query",
                "query_rewrite",
                "reference_movies",
                "moods",
                "themes",
                "genres",
                "pacing",
                "tone",
                "avoid",
                "constraints",
                "confidence",
                "parser_notes",
            ],
            "properties": {
                "raw_query": {
                    "type": "string",
                    "description": "The original user query.",
                },
                "query_rewrite": {
                    "type": "string",
                    "description": (
                        "A concise semantic-search query preserving the user's "
                        "main intent, mood, themes, constraints, and references."
                    ),
                },
                "reference_movies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Movie titles explicitly mentioned by the user.",
                },
                "moods": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mood words such as lonely, warm, tense, melancholic.",
                },
                "themes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Themes such as memory, identity, grief, friendship.",
                },
                "genres": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Genres explicitly requested or strongly implied.",
                },
                "pacing": {
                    "type": ["string", "null"],
                    "description": "Desired pacing, such as slow, medium, fast, or null.",
                },
                "tone": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tone descriptors such as hopeful, dark, funny.",
                },
                "avoid": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Things the user wants to avoid.",
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Other constraints, such as not too long or family-friendly.",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence in the parsed intent.",
                },
                "parser_notes": {
                    "type": "string",
                    "description": "Brief explanation of parsing choices.",
                },
            },
        }