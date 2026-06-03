import type { MovieRecommendation, UserMoviePreferenceResponse} from "@/types/movie";
import { MovieCard } from "./MovieCard";

type RecommendationListProps = {
    results: MovieRecommendation[];
    latencyMs: number | null;
    userId: string;
    query: string | null;
    onPreferenceSaved?: (feedback: UserMoviePreferenceResponse) => void;
};

export function RecommendationList({
    results, 
    latencyMs,
    userId,
    query,
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
      </div>

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