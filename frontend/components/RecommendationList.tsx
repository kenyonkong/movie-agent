import type { MovieRecommendation, UserMoviePreferenceResponse} from "@/types/movie";
import { MovieCard } from "./MovieCard";

type RecommendationListProps = {
    results: MovieRecommendation[];
    latencyMs: number | null;
    candidateCount: number | null;
    filteredWatchedCount: number | null;
    includeWatched: boolean;
    explanationProvider: string | null;
    userId: string;
    query: string | null;
    onPreferenceSaved?: (feedback: UserMoviePreferenceResponse) => void;
};

export function RecommendationList({
    results, 
    latencyMs,
    candidateCount,
    filteredWatchedCount,
    includeWatched,
    userId,
    query,
    explanationProvider,
    onPreferenceSaved,
}: RecommendationListProps) {
    if (results.length === 0) {
        return null;
    }

    return (
    <section className="mt-8">
      <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">
            Recommendations ({results.length})
          </h2>
          <p className="text-sm text-slate-400">
            Ranked by semantic similarity from your local vector database.
          </p>
        </div>

        {latencyMs !== null && (
          <p className="rounded-full border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300">
            Latency: {latencyMs.toFixed(2)} ms
          </p>
        )}
        
        {candidateCount !== null && (
          <p className="rounded-full border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300">
            Candidates: {candidateCount}
          </p>
        )}

        {filteredWatchedCount !== null && !includeWatched && (
          <p className="rounded-full border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300">
            Watched filtered: {filteredWatchedCount}
          </p>
        )}

        {includeWatched && (
          <p className="rounded-full border border-purple-800 bg-purple-950/40 px-4 py-2 text-sm text-purple-200">
            Including watched
          </p>
        )}
      </div>

      {explanationProvider && (
        <p className="rounded-full border border-cyan-800 bg-cyan-950/40 px-4 py-2 text-sm text-cyan-200">
          Explanations provided by: {explanationProvider}
        </p>
      )}
      
      <div className="space-y-5">
        {results.map((movie, index) => (
          <MovieCard
            key={movie.movie_id}
            movie={movie}
            rank={index + 1}
            userId={userId}
            query={query}
            onPreferenceSaved={onPreferenceSaved}
          />
        ))}
      </div>
    </section>
  );
}