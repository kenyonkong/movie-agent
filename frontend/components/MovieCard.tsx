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
        </div>

        <div className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-right">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
            Score
          </p>
          <p className="text-xl font-bold text-cyan-300">
            {formatScore(movie.score)}
          </p>
        </div>
      </div>

      <div className="mb-4 rounded-2xl border border-slate-800 bg-slate-950 p-4">
        <p className="mb-2 text-sm font-semibold text-slate-200">
          Why this was recommended
        </p>
        <p className="text-sm leading-6 text-slate-400">{movie.reason}</p>
      </div>

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