import type { MovieRecommendation, UserMoviePreferenceResponse } from "@/types/movie";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import Image from "next/image"; 

type MovieCardProps = {
    movie: MovieRecommendation;
    rank: number;
    userId: string;
    query: string | null;
    onPreferenceSaved?: (feedback: UserMoviePreferenceResponse) => void;
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
  return (
    <article className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/80 shadow-xl transition hover:border-cyan-500/60">
      <div className="flex flex-col md:flex-row">
        {/* Vertical poster */}
        <div className="relative aspect-[2/3] w-full shrink-0 bg-slate-950 md:w-72">
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
            <div className="flex h-full min-h-72 items-center justify-center p-6 text-center text-sm text-slate-500">
              No poster available
            </div>
          )}
        </div>

        {/* Right content panel */}
        <div className="relative min-w-0 flex-1 overflow-hidden bg-slate-900">
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
                className="object-cover object-center"
              />

              {/* Keep the image visible */}
              <div className="absolute inset-0 bg-slate-950/30" />

              {/* Preserve text readability near the title */}
              <div className="absolute inset-0 bg-gradient-to-r from-slate-950/80 via-slate-950/45 to-transparent" />

              {/* Preserve readability near the bottom */}
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent" />
            </div>
          )}

          {/* All visible content must be above the backdrop */}
          <div className="relative z-10 p-6">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <div className="mb-2 flex items-start gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-slate-950">
                    {rank}
                  </span>

                  <h2 className="min-w-0 text-2xl font-bold text-slate-100">
                    {movie.title}
                  </h2>
                </div>

                <p className="text-sm text-slate-300">
                  {movie.release_year ?? "Unknown year"}
                  {movie.genres ? ` · ${movie.genres}` : ""}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  {movie.vote_average !== null &&
                    `Rating: ${movie.vote_average.toFixed(1)}`}

                  {movie.vote_count !== null &&
                    ` · Votes: ${movie.vote_count}`}

                  {movie.popularity !== null &&
                    ` · Popularity: ${movie.popularity.toFixed(1)}`}
                </p>

                <div className="mt-3 flex flex-wrap gap-2">
                  {movie.preference === "like" && (
                    <span className="rounded-full border border-cyan-400/50 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300 backdrop-blur-sm">
                      Liked
                    </span>
                  )}

                  {movie.preference === "dislike" && (
                    <span className="rounded-full border border-red-400/50 bg-red-400/10 px-3 py-1 text-xs text-red-300 backdrop-blur-sm">
                      Disliked
                    </span>
                  )}

                  {movie.watched && (
                    <span className="rounded-full border border-purple-400/50 bg-purple-400/10 px-3 py-1 text-xs text-purple-300 backdrop-blur-sm">
                      Watched
                    </span>
                  )}

                  {movie.saved && (
                    <span className="rounded-full border border-yellow-400/50 bg-yellow-400/10 px-3 py-1 text-xs text-yellow-300 backdrop-blur-sm">
                      Saved
                    </span>
                  )}
                   {movie.heuristic_rank != null && (
                    <span className="rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1 text-xs text-slate-300 backdrop-blur-sm">
                      Heuristic rank #{movie.heuristic_rank}
                    </span>
                  )}

                  {movie.llm_rank != null && (
                    <span className="rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1 text-xs text-purple-200 backdrop-blur-sm">
                      LLM rank #{movie.llm_rank}
                    </span>
                  )}
                </div>
              </div>

              {/* Ranking summary */}
              <div className="grid shrink-0 gap-2 rounded-2xl border border-slate-700/90 bg-slate-950/80 px-4 py-3 text-right shadow-lg backdrop-blur-sm">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                    Final
                  </p>

                  <p className="text-xl font-bold text-cyan-300">
                    {formatScore(movie.score)}
                  </p>
                </div>
                
                <div className="text-xs text-slate-300">
                  Semantic: {formatScore(movie.semantic_score)}
                </div>

                <div className="text-xs text-slate-300">
                  Preference: {movie.preference_score.toFixed(2)}
                </div>

                <div className="text-xs text-slate-300">
                  Novelty: {movie.novelty_score.toFixed(2)}
                </div>

                <div className="text-xs text-slate-300">
                  Diversity penalty:{" "}
                  {movie.diversity_penalty.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="mb-4 rounded-2xl border border-slate-700/80 bg-slate-950/80 p-4 shadow-lg backdrop-blur-sm">
              <p className="mb-2 text-sm font-semibold text-slate-100">
                Explanation
              </p>

              <p className="text-sm leading-6 text-slate-300">
                {movie.reason}
              </p>
            </div>

            {/* Bounded LLM reranking reason */}
            {movie.llm_rerank_reason && (
              <div className="mb-4 rounded-2xl border border-purple-500/30 bg-purple-950/30 p-4 shadow-lg backdrop-blur-sm">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-300">
                  Bounded LLM reranker
                </p>

                <p className="mt-2 text-sm leading-6 text-slate-200">
                  {movie.llm_rerank_reason}
                </p>
              </div>
            )}

            {/* Ranking signals */}
            <details className="group mb-3">
              <summary className="cursor-pointer text-sm font-medium text-cyan-300 transition hover:text-cyan-200">
                Show ranking signals
              </summary>

              <pre className="mt-3 overflow-x-auto rounded-2xl border border-slate-700/80 bg-slate-950/85 p-4 text-xs leading-6 text-slate-300 shadow-lg backdrop-blur-sm">
                {JSON.stringify(movie.ranking_signals, null, 2)}
              </pre>
            </details>

            {/* Retrieved movie document */}
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-cyan-300 transition hover:text-cyan-200">
                Show retrieved document preview
              </summary>

              <p className="mt-3 whitespace-pre-line rounded-2xl border border-slate-700/80 bg-slate-950/85 p-4 text-sm leading-6 text-slate-300 shadow-lg backdrop-blur-sm">
                {movie.document_preview}
              </p>
            </details>

            {/* User feedback controls */}
            <FeedbackButtons
              movie={movie}
              userId={userId}
              query={query}
              onFeedbackSaved={onPreferenceSaved}
            />
          </div>
        </div>
      </div>
    </article>
  );
}

