import type { MovieRecommendation, UserMoviePreferenceResponse } from "@/types/movie";
import { FeedbackButtons } from "@/components/FeedbackButtons";

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

export function MovieCard({ movie, rank, userId, query, onPreferenceSaved }: MovieCardProps) {
    return (
    <article className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl transition hover:border-cyan-500/60">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-slate-950">
              {rank}
            </span>
            <h2 className="text-2xl font-bold text-slate-100">
              {movie.title}
            </h2>
          </div>

          <p className="text-sm text-slate-400">
            {movie.release_year ?? "Unknown year"}
            {movie.genres ? ` · ${movie.genres}` : ""}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {movie.preference === "like" && (
              <span className="rounded-full border border-cyan-400/50 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
                Liked
              </span>
            )}

            {movie.preference === "dislike" && (
              <span className="rounded-full border border-red-400/50 bg-red-400/10 px-3 py-1 text-xs text-red-300">
                Disliked
              </span>
            )}
            
            {movie.watched && (
              <span className="rounded-full border border-purple-400/50 bg-purple-400/10 px-3 py-1 text-xs text-purple-300">
                Watched
              </span>
            )}
            {movie.saved && (
              <span className="rounded-full border border-yellow-400/50 bg-yellow-400/10 px-3 py-1 text-xs text-yellow-300">
                Saved
              </span>
            )}
          </div>
        </div>


        <div className="grid gap-2 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-right">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
              Final
            </p>
            <p className="text-xl font-bold text-cyan-300">
              {formatScore(movie.score)}
            </p>
          </div>

          <div className="text-xs text-slate-400">
            Semantic: {formatScore(movie.semantic_score)}
          </div>

          <div className="text-xs text-slate-400">
            Preference: {movie.preference_score.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="mb-4 rounded-2xl border border-slate-800 bg-slate-950 p-4">
        <p className="mb-2 text-sm font-semibold text-slate-200">
          Why this was recommended
        </p>
        <p className="text-sm leading-6 text-slate-400">{movie.reason}</p>
      </div>
      
      <details className="group mb-3">
        <summary className="cursor-pointer text-sm font-medium text-cyan-300 transition hover:text-cyan-200">
          Show ranking signals
        </summary>
        <pre className="mt-3 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-slate-400">
          {JSON.stringify(movie.ranking_signals, null, 2)}
        </pre>
      </details>

      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-cyan-300 transition hover:text-cyan-200">
          Show retrieved document preview
        </summary>
        <p className="mt-3 whitespace-pre-line rounded-2xl border border-slate-800 bg-slate-950 p-4 text-sm leading-6 text-slate-400">
          {movie.document_preview}
        </p>
      </details>

      <FeedbackButtons
        movie={movie}
        userId={userId}
        query={query}
        onFeedbackSaved={onPreferenceSaved}
      />
    </article>
  );
}