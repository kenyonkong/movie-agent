from typing import Any

from openai import OpenAI

from app.core.config import settings

class ExplanationService:
    """
    Generates grounded explanations for already-retrieved recommendations.

    Important design principle:
    The LLM does not choose movies.
    The recommender chooses movies.
    The LLM only explains the selected movies using provided metadata.
    """

    def __init__(self) -> None:
        self.provider = settings.explanation_provider.lower().strip()
        self.model = settings.openai_explanation_model

        self.client: OpenAI | None = None

        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is required for the OpenAI explanation provider.")
            
            self.client = OpenAI(api_key=settings.openai_api_key)
    
    
    def get_provider_name(
            self,  
            use_llm_explanation: bool,
    ) -> str:
        if use_llm_explanation and self.provider == "openai":
            return f"openai:{self.model}"
    
        return "template"
    

    def generate_explanations(
            self, 
            query: str, 
            recommendations: list[dict[str, Any]],
            use_llm_explanation: bool,
    ) -> list[str]:
        """
        Generate one explanation per recommendation.

        Falls back to template explanations if:
        - use_llm_explanations is false
        - provider is not openai
        - OpenAI request fails
        """
        if not use_llm_explanation or self.provider != "openai":
            return [
                self._generate_template_explanation(query, item)
                for item in recommendations
            ]

        try:
            return self._generate_openai_explanations(
                query, 
                recommendations
            )
        except Exception:
            # If OpenAI fails, fall back to template explanations
            return [
                self._generate_template_explanation(query, item)
                for item in recommendations
            ]
        
    
    def _generate_template_explanation(self, 
        query: str, 
        item: dict[str, Any]
    ) -> str:
        title = item.get("title") or "This movie"
        genres = item.get("genres")
        semantic_score = float(item.get("semantic_score", 0.0))
        preference_score = float(item.get("preference_score", 0.0))
        novelty_score = float(item.get("novelty_score", 0.0))
        diversity_penalty = float(item.get("diversity_penalty", 0.0))
        watched = bool(item.get("watched", False))
        saved = bool(item.get("saved", False))

        parts: list[str] = [
            f"{title} was selected because it semantically matches your query "
            f"with a semantic score of {semantic_score:.2f}."
        ]

        if genres:
            parts.append(f"Its genres include {genres}.")

        if preference_score > 0:
            parts.append(
                f"It also received a positive preference signal from your liked genres "
                f"(preference score: {preference_score:.2f})."
            )
        elif preference_score < 0:
            parts.append(
                f"It overlaps with some disliked genre signals "
                f"(preference score: {preference_score:.2f}), so it was penalized."
            )

        if novelty_score > 0.3:
            parts.append(
                "It received a small novelty boost because it is less obvious than very high-popularity candidates."
            )

        if diversity_penalty > 0:
            parts.append(
                "It received a diversity penalty because it overlaps with other selected results."
            )

        if watched:
            parts.append("It was penalized because you marked it as watched.")

        if saved:
            parts.append("It received a small boost because you saved it.")

        return " ".join(parts)
    

    def _generate_openai_explanations(
        self,
        query: str,
        recommendations: list[dict[str, Any]]
    ) -> list[str]:
        """
        Generate explanations using OpenAI.

        The prompt instructs the model to explain only the provided movies.
        """
        if self.client is None:
            raise ValueError("OpenAI client is not initialized.")

        prompt = self._build_prompt(
            query = query, 
            recommendations = recommendations
        )

        response = self.client.responses.create(
            model=self.model,
            input=prompt, 
            temperature=0.3
        )

        output_text = response.output_text.strip()

        explanations = self._parse_numbered_explanations(
            output_text=output_text, 
            expected_count=len(recommendations),
        )

        if len(explanations) != len(recommendations):
            raise ValueError("Number of generated explanations does not match the number of recommendations.")

        return explanations
    

    def _build_prompt(
        self,
        query: str,
        recommendations: list[dict[str, Any]]
    ) -> str:
        """
        Build the prompt for the OpenAI API.
        """
        movie_blocks: list[str] = []

        for index, item in enumerate(recommendations, start=1):
            ranking_signals = item.get("ranking_signals", {})
            block = f"""
Movie {index}
Title: {item.get("title")}
Year: {item.get("release_year")}
Genres: {item.get("genres")}
Watched: {item.get("watched")}
Saved: {item.get("saved")}

Scores:
- Final score: {item.get("final_score")}
- Base score: {ranking_signals.get("base_score")}
- Semantic score: {item.get("semantic_score")}
- Preference score: {item.get("preference_score")}
- Novelty score: {item.get("novelty_score")}
- Diversity penalty: {item.get("diversity_penalty")}
- Saved boost: {ranking_signals.get("saved_boost")}
- Watched penalty: {ranking_signals.get("watched_penalty")}

Score meanings:
- Semantic score means how closely the movie metadata matched the user's query.
- Preference score means how much the movie's genres overlap with the user's liked or disliked genre memory.
- Novelty score is a small boost for less obvious movies, based on popularity and vote count.
- Diversity penalty is subtracted when this movie overlaps too much with other selected results.
- Saved boost is added if the user previously saved this movie.
- Watched penalty is subtracted if the user already marked this movie as watched.

Ranking formula:
base_score =
  0.70 * semantic_score
+ 0.15 * preference_score
+ 0.10 * novelty_score
+ saved_boost
- watched_penalty

final_score =
  base_score
- diversity_penalty

diversity_penalty is based on maximum Jaccard similarity between the candidate's genres and any selected movie's genres.

Document preview:
{item.get("document_preview") or item.get("document") or ""}
""".strip()
            movie_blocks.append(block)
        
        movies_text = "\n\n".join(movie_blocks)

        return f"""
You are writing grounded explanations for a movie recommendation system.

Important:
You are NOT choosing movies.
You are NOT recommending new movies.
You are only explaining why the already-selected movies were recommended.

User query:
{query}

Recommended movies and metadata:
{movies_text}

How the recommendation system works:
1. The system first retrieves movie candidates from a vector database using semantic similarity.
2. It then reranks candidates using user memory, watched status, saved status, novelty, and diversity.
3. The final movies shown to the user have already been selected by the recommender.
4. Your job is to explain the recommendation clearly and faithfully.

Explanation requirements:
- Use only the provided movie metadata, document preview, and ranking signals.
- Do not invent movie facts.
- Do not recommend movies outside the provided list.
- Explain why the movie matches the user's query.
- Explain which ranking signals helped or hurt the movie when useful.
- If preference score is positive, mention that it likely matched the user's stored taste.
- If preference score is negative, mention that it may conflict with stored taste.
- If novelty score is meaningful, explain that it may be a less obvious recommendation.
- If diversity penalty is nonzero, explain that it overlapped with other selected results.
- If watched is true, mention that it was already watched and may have been penalized.
- If saved is true, mention that it received a saved boost.
- Do not mechanically list every score.
- Write naturally, but stay faithful to the evidence.
- Keep each explanation to 4-6 sentences.
- Write one explanation per movie.
- Output exactly {len(recommendations)} numbered explanations.
- Use this exact format:

1. explanation text
2. explanation text
3. explanation text
""".strip()


    def _parse_numbered_explanations(
        self,
        output_text: str,
        expected_count: int
    ) -> list[str]:
        """
        Parse a numbered list like:
        1. text
        2. text

        This is intentionally simple. Later, we can switch to structured outputs.
        """
        explanations: list[str] = []

        current_parts: list[str] = []

        for line in output_text.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            is_new_item = any(
                stripped.startswith(f"{index}.")
                for index in range(1, expected_count + 1)
            )

            if is_new_item:
                if current_parts:
                    explanations.append(" ".join(current_parts).strip())
                    current_parts = []
                
                # Remove leading number and period, e.g., "1."
                _, _, rest = stripped.partition(".")
                current_parts = [rest.strip()]
            else:
                current_parts.append(stripped)
            
        if current_parts:
                explanations.append(" ".join(current_parts).strip())
            
        return explanations
            