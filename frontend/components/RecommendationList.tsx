import type { 
  MovieIntent, 
  MovieRecommendation, 
  UserMoviePreferenceResponse, 
  AgentTrace,
} from "@/types/movie";

import { AgentTracePanel } from "./AgentTracePanel";
import { MovieCard } from "./MovieCard";

type RecommendationListProps = {
    results: MovieRecommendation[];
    latencyMs: number | null;
    candidateCount: number | null;
    filteredWatchedCount: number | null;
    includeWatched: boolean;
    explanationProvider: string | null;
    intentProvider: string | null;
    retrievalQuery: string | null;
    parsedIntent: MovieIntent | null;
    userId: string;
    query: string | null;
    onPreferenceSaved?: (feedback: UserMoviePreferenceResponse) => void;
    agentTrace: AgentTrace | null;
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
    intentProvider,
    retrievalQuery,
    parsedIntent,
    onPreferenceSaved,
    agentTrace,
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
      
      {agentTrace && (
        <AgentTracePanel trace={agentTrace} />
      )}

      {parsedIntent && (
        <section className="mb-5 rounded-3xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="mb-3">
            <h3 className="text-lg font-bold text-slate-100">
              Parsed Intent
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              The raw query was converted into structured intent before vector retrieval.
            </p>
          </div>

          <div className="mb-3 flex flex-wrap gap-2">
            {intentProvider && (
              <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                Intent: {intentProvider}
              </span>
            )}

            {retrievalQuery && (
              <span className="rounded-full border border-cyan-700 bg-cyan-950/40 px-3 py-1 text-xs text-cyan-200">
                Retrieval query: {retrievalQuery}
              </span>
            )}
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <p className="mb-2 text-sm font-semibold text-cyan-300">
                Reference movies
              </p>
              <p className="text-sm text-slate-400">
                {parsedIntent.reference_movies.length > 0
                  ? parsedIntent.reference_movies.join(", ")
                  : "None"}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <p className="mb-2 text-sm font-semibold text-purple-300">
                Moods / tone
              </p>
              <p className="text-sm text-slate-400">
                {[...parsedIntent.moods, ...parsedIntent.tone].length > 0
                  ? [...parsedIntent.moods, ...parsedIntent.tone].join(", ")
                  : "None"}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <p className="mb-2 text-sm font-semibold text-green-300">
                Themes / genres
              </p>
              <p className="text-sm text-slate-400">
                {[...parsedIntent.themes, ...parsedIntent.genres].length > 0
                  ? [...parsedIntent.themes, ...parsedIntent.genres].join(", ")
                  : "None"}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <p className="mb-2 text-sm font-semibold text-red-300">
                Avoid / constraints
              </p>
              <p className="text-sm text-slate-400">
                {[...parsedIntent.avoid, ...parsedIntent.constraints].length > 0
                  ? [...parsedIntent.avoid, ...parsedIntent.constraints].join(", ")
                  : "None"}
              </p>
            </div>
          </div>

          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-medium text-cyan-300">
              Show raw intent JSON
            </summary>
            <pre className="mt-3 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-slate-400">
              {JSON.stringify(parsedIntent, null, 2)}
            </pre>
          </details>
        </section>
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