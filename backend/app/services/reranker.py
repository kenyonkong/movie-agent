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

    Day 9 version:
    - watched movie filtering or penalty added to Day 8 version

     Day 10 version:
    - novelty score from popularity/vote_count
    - diversity penalty based on genre overlap with already selected movies

    This is a transparent heuristic reranker, not a learned model.
    """

    SEMANTIC_WEIGHT = 0.75
    PREFERENCE_WEIGHT = 0.15
    NOVELTY_WEIGHT = 0.1
    DIVERSITY_WEIGHT = 0.12

    SAVED_WEIGHT = 0.1
    WATCHED_PENALTY = 0.15


    def filter_watched_candidates(
            self,
            candidates: list[dict[str, Any]],
            user_memory: dict,
            include_watched: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Optionally remove watched movies from the candidate pool.

        Returns:
            filtered_candidates, filtered_watched_count
        """
        if include_watched:
            return candidates, 0
        
        watched_movie_ids = user_memory.get("watched_movie_ids", set())
        filtered_candidates = [
            candidate for candidate in candidates
            if str(candidate.get("id")) not in watched_movie_ids
        ]
        filtered_watched_count = len(candidates) - len(filtered_candidates)
        return filtered_candidates, filtered_watched_count


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
            key=lambda x: x["base_score"],
            reverse=True
        )
        return self._select_diverse_top_k(reranked_candidates, top_k)
    

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

        novelty_score = self._compute_novelty_score(
            popularity=float(candidate.get("popularity", 0.0) or 0.0),
            vote_count=float(candidate.get("vote_count", 0) or 0),
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

        base_score = (
            semantic_score * self.SEMANTIC_WEIGHT
            + preference_score * self.PREFERENCE_WEIGHT
            + novelty_score * self.NOVELTY_WEIGHT
            + saved_boost
            - watched_penalty
        )

        base_score = max(0.0, min(1.0, base_score))

        candidate["semantic_score"] = round(semantic_score, 4)
        candidate["preference_score"] = round(preference_score, 4)
        candidate["novelty_score"] = round(novelty_score, 4)
        candidate["saved"] = saved
        candidate["watched"] = watched
        candidate["preference"] = preference
        candidate["base_score"] = round(base_score, 4)

        # to be filled later during diversity-aware selection
        candidate["diversity_penalty"] = 0.0
        candidate["final_score"] = round(base_score, 4)

        candidate["ranking_signals"] = {
            "semantic_score": round(semantic_score, 4),
            "preference_score": round(preference_score, 4),
            "novelty_score": round(novelty_score, 4),
            "saved_boost": round(saved_boost, 4),
            "watched_penalty": round(watched_penalty, 4),
            "diversity_penalty": 0.0,
            "base_score": round(base_score, 4),
            "final_score": round(base_score, 4),
            "watched": watched,
            "saved": saved,
            "preference": preference or "none",
        }
        return candidate 
    

    def _select_diverse_top_k(
            self,
            candidates: list[dict[str, Any]],
            top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Select top-k candidates while penalizing genre overlap.

        This is a greedy diversification algorithm.

        At each step:
        - compute diversity penalty against already selected movies
        - subtract the penalty from the base score
        - select the candidate with the best adjusted score
        """
        selected: list[dict[str, Any]] = []
        remaining = candidates.copy()

        while remaining and len(selected) < top_k:
            best_candidate = None
            best_adjusted_score = float("-inf")
            best_penalty = 0.0

            for candidate in remaining:
                diversity_penalty = self._compute_diversity_penalty(candidate, selected)
                adjusted_score = candidate["base_score"] - diversity_penalty

                if adjusted_score > best_adjusted_score:
                    best_adjusted_score = adjusted_score
                    best_candidate = candidate
                    best_penalty = diversity_penalty

            if best_candidate is None:
                break

            final_score = max(0.0, min(1.0, best_adjusted_score))

            best_candidate["diversity_penalty"] = round(best_penalty, 4)
            best_candidate["final_score"] = round(final_score, 4)

            reranking_signals = best_candidate.get("ranking_signals", {})
            reranking_signals["diversity_penalty"] = round(best_penalty, 4)
            reranking_signals["final_score"] = round(final_score, 4)
            best_candidate["ranking_signals"] = reranking_signals

            selected.append(best_candidate)
            remaining.remove(best_candidate)

        return selected
    


    def _compute_diversity_penalty(
        self,
        candidate: dict[str, Any],
        selected: list[dict[str, Any]],
    ) -> float:
        """
        Penalize candidates that share many genres with already selected movies.

        The penalty is based on maximum Jaccard similarity between the candidate's
        genres and any selected movie's genres.

        Jaccard similarity:
            intersection_size / union_size

        Example:
            Candidate genres: {Drama, Sci-Fi}
            Selected genres:  {Drama, Romance}
            intersection = {Drama}
            union = {Drama, Sci-Fi, Romance}
            similarity = 1 / 3
        """
        if not selected:
            return 0.0
        
        candidate_genres = set(self._parse_genres(candidate.get("genres", "") or ""))

        if not candidate_genres:
            return 0.0

        max_similarity = 0.0

        for selected_movie in selected:
            selected_genres = set(self._parse_genres(selected_movie.get("genres", "") or ""))
            if not selected_genres:
                continue
            
            intersection_size = len(candidate_genres & selected_genres)
            union_size = len(candidate_genres | selected_genres)

            if union_size == 0:
                continue

            jaccard = intersection_size / union_size
            max_similarity = max(max_similarity, jaccard)
        
        return max_similarity * self.DIVERSITY_WEIGHT



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

        liked_score = 0.0
        disliked_score = 0.0

        for genre in movie_genres:
            liked_score += liked_genres.get(genre, 0) / liked_total
            disliked_score += disliked_genres.get(genre, 0) / disliked_total
    
        raw_score = liked_score - disliked_score
        # Normalize to roughly [-1, 1]
        return max(-1.0, min(1.0, raw_score))
    

    def _compute_novelty_score(
        self,
        popularity: float,
        vote_count: float,
    ) -> float:
        """
        Compute a small novelty score.

        Idea:
        - Extremely popular movies are less novel.
        - Less popular movies are more novel.
        - But movies with almost no votes should not get maximum novelty,
          because they may be low-quality or too obscure.

        This is a heuristic, not a perfect measure.
        """
        popularity = max(0.0, popularity)
        vote_count = max(0.0, vote_count)

        # Popularity penalty:
        # popularity around 0 gives high novelty.
        # very high popularity gives low novelty.
        popularity_novelty = 1.0 / (1.0 + popularity / 50.0)

        # Confidence factor:
        # very low vote_count gives lower confidence.
        # this prevents extremely obscure movies from always winning.
        vote_confidence = min(1.0, vote_count / 500.0)

        novelty_score = popularity_novelty * vote_confidence

        return max(0.0, min(1.0, novelty_score))



    def _parse_genres(self, genres: str) -> list[str]:
        """
        Parse genres string into a list of genres.
        Example:
            "Action, Comedy, Drama" -> ["Action", "Comedy", "Drama"]
        """
        if not genres:
            return []
        
        return [genre.strip() for genre in genres.split(",") if genre.strip()]
