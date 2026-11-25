import type { MovieRecommendation, UserMoviePreferenceResponse } from "@/types/movie";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { MovieReviewPanel } from "@/components/MovieReviewPanel";
import { useReviews } from "@/components/ReviewsProvider";
import Image from "next/image"; 

type MovieCardProps = {
    movie: MovieRecommendation;
    rank: number;
    userId: string;
    query: string | null;
    onPreferenceSaved: (feedback: UserMoviePreferenceResponse) => void;
};

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function MovieCard({
  movie,
  rank,
  userId,
  query,
  onPreferenceSaved,
}: MovieCardProps) {
  const { reviews } = useReviews();
  const watched = movie.watched || reviews.some(
    (review) => review.movie_id === movie.movie_id && review.watched,
  );

  return (
    <article className="surface-card overflow-hidden rounded-[2rem] transition duration-300 hover:-translate-y-1 hover:border-[#CE8946]/70 hover:shadow-[0_26px_64px_rgba(91,72,30,0.18)]">
      <div className="flex flex-col md:flex-row">
        {/* Vertical poster */}
        <div className="relative aspect-[2/3] w-full shrink-0 bg-[#E8DCA1] md:w-72">
          {movie.poster_url ? (
            <Image
              src={movie.poster_url}
              alt={`${movie.title} poster`}
              fill
              sizes="(max-width: 768px) 100vw, 288px"
              className="object-cover"
              priority={rank <= 2}
            />
          ) : (
            <div className="flex h-full min-h-72 items-center justify-center bg-[linear-gradient(145deg,#FDFBD4,#BDB76B)] p-6 text-center text-sm font-semibold text-[#625845]">
              No poster available
            </div>
          )}
        </div>

        {/* Right content panel */}
        <div className="relative min-w-0 flex-1 overflow-hidden bg-[#FFFDF0]">
          {/* Backdrop image */}
          {movie.backdrop_url && (
            <div
              className="pointer-events-none absolute inset-0"
              aria-hidden="true"
            >
              <Image
                src={movie.backdrop_url}
                alt=""
                fill
                sizes="(max-width: 768px) 100vw, 1200px"
                className="object-cover object-center opacity-20 saturate-75"
              />

              {/* Keep the image visible */}
              <div className="absolute inset-0 bg-[#FDFBD4]/30" />

              {/* Preserve text readability near the title */}
              <div className="absolute inset-0 bg-gradient-to-r from-[#FFFDF0] via-[#FFFDF0]/90 to-[#FDFBD4]/65" />

              {/* Preserve readability near the bottom */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#FFFDF0]/85 via-transparent to-[#D4AF37]/10" />
            </div>
          )}

          {/* All visible content must be above the backdrop */}
          <div className="relative z-10 p-6">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <div className="mb-2 flex items-start gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#B86F32] bg-[#CE8946] text-sm font-bold text-[#2F251A] shadow-sm">
                    {rank}
                  </span>

                  <h2 className="font-display min-w-0 text-3xl font-semibold text-[#352D22]">
                    {movie.title}
                  </h2>
                </div>

                <p className="text-sm font-medium text-[#625845]">
                  {movie.release_year ?? "Unknown year"}
                  {movie.genres ? ` · ${movie.genres}` : ""}
                </p>

                <p className="mt-2 text-xs text-[#776B51]">
                  {movie.vote_average !== null &&
                    `Rating: ${movie.vote_average.toFixed(1)}`}

                  {movie.vote_count !== null &&
                    ` · Votes: ${movie.vote_count}`}

                  {movie.popularity !== null &&
                    ` · Popularity: ${movie.popularity.toFixed(1)}`}

                  {movie.runtime !== null &&
                    ` · Runtime: ${movie.runtime} min`}

                </p>

                <div className="mt-3 flex flex-wrap gap-2">
                  {movie.preference === "like" && (
                    <span className="rounded-full border border-[#BDB76B] bg-[#BDB76B]/20 px-3 py-1 text-xs font-semibold text-[#5E5A31] backdrop-blur-sm">
                      Liked
                    </span>
                  )}

                  {movie.preference === "dislike" && (
                    <span className="rounded-full border border-[#B86B4B]/60 bg-[#CE8946]/15 px-3 py-1 text-xs font-semibold text-[#814526] backdrop-blur-sm">
                      Disliked
                    </span>
                  )}

                  {watched && (
                    <span className="rounded-full border border-[#BDB76B]/80 bg-[#FDFBD4]/80 px-3 py-1 text-xs font-semibold text-[#5E5A31] backdrop-blur-sm">
                      Watched
                    </span>
                  )}

                  {movie.saved && (
                    <span className="rounded-full border border-[#D4AF37]/80 bg-[#D4AF37]/15 px-3 py-1 text-xs font-semibold text-[#735B0E] backdrop-blur-sm">
                      Saved
                    </span>
                  )}
                   {movie.heuristic_rank != null && (
                    <span className="rounded-full border border-[#BDB76B]/60 bg-[#FFFDF0]/80 px-3 py-1 text-xs text-[#706453] backdrop-blur-sm">
                      Heuristic rank #{movie.heuristic_rank}
                    </span>
                  )}

                  {movie.llm_rank != null && (
                    <span className="rounded-full border border-[#CE8946]/55 bg-[#CE8946]/10 px-3 py-1 text-xs text-[#7C4A21] backdrop-blur-sm">
                      LLM rank #{movie.llm_rank}
                    </span>
                  )}
                </div>
              </div>

              {/* Ranking summary */}
              <div className="grid shrink-0 gap-2 rounded-2xl border border-[#D4AF37]/70 bg-[#FDFBD4]/90 px-4 py-3 text-right shadow-[0_8px_20px_rgba(91,72,30,0.10)] backdrop-blur-sm">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#826714]">
                    Final
                  </p>

                  <p className="font-display text-2xl font-semibold text-[#594713]">
                    {formatScore(movie.score)}
                  </p>
                </div>
                
                <div className="text-xs text-[#625845]">
                  Semantic: {formatScore(movie.semantic_score)}
                </div>

                <div className="text-xs text-[#625845]">
                  Preference: {movie.preference_score.toFixed(2)}
                </div>

                <div className="text-xs text-[#625845]">
                  Novelty: {movie.novelty_score.toFixed(2)}
                </div>

                <div className="text-xs text-[#625845]">
                  Diversity penalty:{" "}
                  {movie.diversity_penalty.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="mb-4 rounded-2xl border border-[#BDB76B]/55 bg-[#FFFDF0]/85 p-4 shadow-[0_8px_20px_rgba(91,72,30,0.08)] backdrop-blur-sm">
              <p className="mb-2 text-sm font-bold text-[#8A5B2B]">
                Why it fits
              </p>

              <p className="text-sm leading-7 text-[#544835]">
                {movie.reason}
              </p>
            </div>

            {/* Bounded LLM reranking reason */}
            {movie.llm_rerank_reason && (
              <div className="mb-4 rounded-2xl border border-[#CE8946]/45 bg-[#CE8946]/10 p-4 shadow-sm backdrop-blur-sm">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#8A5B2B]">
                  Bounded LLM reranker
                </p>

                <p className="mt-2 text-sm leading-7 text-[#544835]">
                  {movie.llm_rerank_reason}
                </p>
              </div>
            )}

            {/* Ranking signals */}
            <details className="group mb-3">
              <summary className="cursor-pointer text-sm font-semibold text-[#7C5429] transition hover:text-[#A9662E]">
                Show ranking signals
              </summary>

              <pre className="mt-3 overflow-x-auto rounded-2xl border border-[#BDB76B]/60 bg-[#F5EDC5]/90 p-4 text-xs leading-6 text-[#544835] shadow-sm backdrop-blur-sm">
                {JSON.stringify(movie.ranking_signals, null, 2)}
              </pre>
            </details>

            {/* Retrieved movie document */}
            <details className="group">
              <summary className="cursor-pointer text-sm font-semibold text-[#7C5429] transition hover:text-[#A9662E]">
                Show retrieved document preview
              </summary>

              <p className="mt-3 whitespace-pre-line rounded-2xl border border-[#BDB76B]/60 bg-[#F5EDC5]/90 p-4 text-sm leading-7 text-[#544835] shadow-sm backdrop-blur-sm">
                {movie.document_preview}
              </p>
            </details>

            {/* User feedback controls */}
            <FeedbackButtons
              movie={{ ...movie, watched }}
              userId={userId}
              query={query}
              onFeedbackSaved={onPreferenceSaved}
            />

            <div className="mt-3">
              <MovieReviewPanel movieId={movie.movie_id} title={movie.title} />
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

