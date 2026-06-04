from typing import Any

class MovieReranker:
    """
    Reranks semantic retrieval candidates using user memory.

    Day 8 version:
    - semantic score from vector distance
    - liked genre boost
    - disliked genre penalty
    - watched movie penalty
    - saved movie boost

    This is a transparent heuristic reranker, not a learned model.
    """

    SEMANTIC_WEIGHT = 0.75
    PREFERENCE_WEIGHT = 0.15
    SAVED_WEIGHT = 0.1
    WATCHED_PENALTY = 0.2

    def rerank(
        self,
        candidates: list[dict[str, Any]],
        user_memory: dict,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Rerank candidate movies and return the top_k final results.
        """
        reranked_candidates = [
            self._score_candidate(candidate, user_memory)
            for candidate in candidates
        ]
        # Sort by final score descending

        reranked_candidates.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )
        return reranked_candidates[:top_k]
    
    def _score_candidate(
            self,
            candidate: dict[str, Any],
            user_memory: dict,
    ) -> dict[str, Any]:
        movie_id = str(candidate.get("id"))
        genres_text = candidate.get("genres") or ""

        semantic_score = self._distance_to_score(
            float(candidate.get("distance", 0.0))
        )

        preference_score = self._compute_preference_score(
            genres_text = genres_text,
            liked_genres = user_memory.get("liked_genres", {}),
            disliked_genres = user_memory.get("disliked_genres", {}),
        )

        watched = movie_id in user_memory.get("watched_movie_ids", set())
        saved = movie_id in user_memory.get("saved_movie_ids", set())

        liked = movie_id in user_memory.get("liked_movie_ids", set())
        disliked = movie_id in user_memory.get("disliked_movie_ids", set())

        preference: str | None = None
        if liked:
            preference = "like"
        elif disliked:
            preference = "dislike"

        saved_boost = self.SAVED_WEIGHT if saved else 0.0
        watched_penalty = self.WATCHED_PENALTY if watched else 0.0

        final_score = (
            semantic_score * self.SEMANTIC_WEIGHT
            + preference_score * self.PREFERENCE_WEIGHT
            + saved_boost
            - watched_penalty
        )

        final_score = max(0.0, min(1.0, final_score))

        candidate["semantic_score"] = round(semantic_score, 4)
        candidate["preference_score"] = round(preference_score, 4)
        candidate["saved"] = saved
        candidate["watched"] = watched
        candidate["preference"] = preference
        candidate["final_score"] = round(final_score, 4)
        candidate["ranking_signals"] = {
            "semantic_score": round(semantic_score, 4),
            "preference_score": round(preference_score, 4),
            "saved_boost": round(saved_boost, 4),
            "watched_penalty": round(watched_penalty, 4),
            "final_score": round(final_score, 4),
            "watched": watched,
            "saved": saved,
            "preference": preference or "none",
        }
        return candidate 
    

    def _distance_to_score(self, distance: float) -> float:
        """
        Convert vector distance to a similarity-style score.

        Lower distance means more similar.
        Higher score means better.
        """
        return 1.0 / (1.0 + max(0.0, distance))


    def _compute_preference_score(
        self,
        genres_text: str,
        liked_genres: dict[str, int],
        disliked_genres: dict[str, int],
    ) -> float:
        """
        Compute genre preference score in range roughly [-1, 1].

        Positive:
            movie overlaps with liked genres

        Negative:
            movie overlaps with disliked genres
        """
        movie_genres = self._parse_genres(genres_text)

        if not movie_genres:
            return 0.0
        
        liked_total = sum(liked_genres.values()) or 1
        disliked_total = sum(disliked_genres.values()) or 1

        liked_score = 0
        disliked_score = 0

        for genre in movie_genres:
            liked_score += liked_genres.get(genre, 0) / liked_total
            disliked_score += disliked_genres.get(genre, 0) / disliked_total
    
        raw_score = liked_score - disliked_score
        # Normalize to roughly [-1, 1]
        return max(-1.0, min(1.0, raw_score))
    

    def _parse_genres(self, genres: str) -> list[str]:
        """
        Parse genres string into a list of genres.
        Example:
            "Action, Comedy, Drama" -> ["Action", "Comedy", "Drama"]
        """
        if not genres:
            return []
        
        return [genre.strip() for genre in genres.split(",") if genre.strip()]
