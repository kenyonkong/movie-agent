import json

from app.agents.movie_agent import MovieAgent
from app.db.database import SessionLocal
from app.db.schemas import RecommendRequest


def main() -> None:
    db = SessionLocal()
    agent = MovieAgent()

    try:
        request = RecommendRequest(
            user_id="demo_user",
            query=(
                "I want something like Her or "
                "After Yang: quiet, emotionally "
                "intelligent, and futuristic, but "
                "not extremely slow or hopeless."
            ),
            top_k=5,
            include_watched=False,
            use_llm_intent=True,
            use_llm_reranker=True,
            use_llm_explanations=False,
            include_agent_trace=True,
        )

        response = agent.recommend(
            db=db,
            request=request,
        )

        print("\n========== PROVIDERS ==========")
        print(
            f"Intent: {response.intent_provider}"
        )
        print(
            f"Reranker: "
            f"{response.reranker_provider}"
        )
        print(
            f"Reranker fallback: "
            f"{response.reranker_fallback_used}"
        )
        print(
            f"Explanations: "
            f"{response.explanation_provider}"
        )

        print("\n========== FINAL RESULTS ==========")

        for index, movie in enumerate(
            response.results,
            start=1,
        ):
            print("\n" + "-" * 80)
            print(
                f"Final position {index}: "
                f"{movie.title}"
            )
            print(
                f"Heuristic rank: "
                f"{movie.heuristic_rank}"
            )
            print(
                f"LLM rank: {movie.llm_rank}"
            )
            print(
                "Heuristic score: "
                f"{movie.score:.4f}"
            )
            print(
                "LLM rationale: "
                f"{movie.llm_rerank_reason}"
            )

        if response.agent_trace:
            print("\n========== TRACE ==========")
            print(
                json.dumps(
                    response.agent_trace.model_dump(),
                    indent=2,
                    ensure_ascii=False,
                )
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()