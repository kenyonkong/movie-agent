import type { 
  MovieIntent, 
  MovieRecommendation, 
  UserMoviePreferenceResponse, 
  AgentTrace,
  ConstraintReport,
} from "@/types/movie";

import { AgentTracePanel } from "./AgentTracePanel";
import { MovieCard } from "./MovieCard";

type RecommendationListProps = {
    results: MovieRecommendation[];
    latencyMs: number | null;
    candidateCount: number | null;
    filteredWatchedCount: number | null;
    includeWatched: boolean;
    rerankerProvider: string | null;
    rerankerFallbackUsed: boolean | null;
    explanationProvider: string | null;
    intentProvider: string | null;
    retrievalQuery: string | null;
    parsedIntent: MovieIntent | null;
    userId: string;
    query: string | null;
    constraintReport: ConstraintReport | null;
    onPreferenceSaved: (feedback: UserMoviePreferenceResponse) => void;
    agentTrace: AgentTrace | null;
};

export function RecommendationList({
    results, 
    latencyMs,
    candidateCount,
    filteredWatchedCount,
    includeWatched,
    rerankerProvider,
    rerankerFallbackUsed,
    userId,
    query,
    explanationProvider,
    intentProvider,
    retrievalQuery,
    parsedIntent,
    onPreferenceSaved,
    agentTrace,
    constraintReport,
}: RecommendationListProps) {
    if (results.length === 0) {
        return null;
    }

    return (
    <section className="mt-8">
      <div className="mb-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="eyebrow mb-2">Curated for you</p>
            <h2 className="font-display text-3xl font-semibold text-[#352D22] md:text-4xl">
              Recommendations ({results.length})
            </h2>
            <p className="mt-1 text-sm text-[#706453]">
              Ranked from the catalog for relevance, preference, and variety.
            </p>
          </div>

          {latencyMs !== null && (
            <p className="w-fit rounded-full border border-[#BDB76B]/65 bg-[#FFFDF0]/70 px-4 py-2 text-sm text-[#625845]">
              Ready in {latencyMs.toFixed(0)} ms
            </p>
          )}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {candidateCount !== null && (
            <p className="rounded-full border border-[#BDB76B]/65 bg-[#FFFDF0]/70 px-4 py-2 text-sm text-[#625845]">
              Candidates: {candidateCount}
            </p>
          )}

          {filteredWatchedCount !== null && !includeWatched && (
            <p className="rounded-full border border-[#BDB76B]/65 bg-[#FFFDF0]/70 px-4 py-2 text-sm text-[#625845]">
              Watched filtered: {filteredWatchedCount}
            </p>
          )}

          {rerankerProvider && (
            <span className="rounded-full border border-[#CE8946]/55 bg-[#CE8946]/10 px-4 py-2 text-sm text-[#75471F]">
              Reranker: {rerankerProvider}
            </span>
          )}

          {rerankerFallbackUsed && (
            <span className="rounded-full border border-[#D4AF37]/70 bg-[#D4AF37]/15 px-4 py-2 text-sm text-[#6A550F]">
              LLM reranker fallback used
            </span>
          )}

          {explanationProvider && (
            <p className="rounded-full border border-[#BDB76B]/65 bg-[#BDB76B]/15 px-4 py-2 text-sm text-[#5E5A31]">
              Explanations: {explanationProvider}
            </p>
          )}

          {includeWatched && (
            <p className="rounded-full border border-[#BDB76B]/65 bg-[#FDFBD4]/80 px-4 py-2 text-sm text-[#5E5A31]">
              Including watched
            </p>
          )}
        </div>
      </div>


      
      {agentTrace && (
        <AgentTracePanel trace={agentTrace} />
      )}

      {parsedIntent && (
        <section className="surface-card mb-5 rounded-3xl p-5">
          <div className="mb-3">
            <h3 className="font-display text-2xl font-semibold text-[#352D22]">
              Parsed Intent
            </h3>
            <p className="mt-1 text-sm text-[#706453]">
              The raw query was converted into structured intent before vector retrieval.
            </p>
          </div>

          <div className="mb-3 flex flex-wrap gap-2">
            {intentProvider && (
              <span className="rounded-full border border-[#BDB76B]/70 px-3 py-1 text-xs text-[#625845]">
                Intent: {intentProvider}
              </span>
            )}

            {retrievalQuery && (
              <span className="rounded-full border border-[#CE8946]/55 bg-[#CE8946]/10 px-3 py-1 text-xs text-[#75471F]">
                Retrieval query: {retrievalQuery}
              </span>
            )}
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
              <p className="mb-2 text-sm font-semibold text-[#826714]">
                Reference movies
              </p>
              <p className="text-sm text-[#706453]">
                {parsedIntent.reference_movies.length > 0
                  ? parsedIntent.reference_movies.join(", ")
                  : "None"}
              </p>
            </div>

            <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
              <p className="mb-2 text-sm font-semibold text-[#6D6940]">
                Moods / tone
              </p>
              <p className="text-sm text-[#706453]">
                {[...parsedIntent.moods, ...parsedIntent.tone].length > 0
                  ? [...parsedIntent.moods, ...parsedIntent.tone].join(", ")
                  : "None"}
              </p>
            </div>

            <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
              <p className="mb-2 text-sm font-semibold text-[#626633]">
                Themes / genres
              </p>
              <p className="text-sm text-[#706453]">
                {[...parsedIntent.themes, ...parsedIntent.genres].length > 0
                  ? [...parsedIntent.themes, ...parsedIntent.genres].join(", ")
                  : "None"}
              </p>
            </div>

            <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
              <p className="mb-2 text-sm font-semibold text-[#9A592E]">
                Avoid / constraints
              </p>
              <p className="text-sm text-[#706453]">
                {[...parsedIntent.avoid, ...parsedIntent.constraints].length > 0
                  ? [...parsedIntent.avoid, ...parsedIntent.constraints].join(", ")
                  : "None"}
              </p>
            </div>
          </div>

          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-semibold text-[#7C5429]">
              Show raw intent JSON
            </summary>
            <pre className="mt-3 overflow-x-auto rounded-2xl border border-[#BDB76B]/60 bg-[#F5EDC5] p-4 text-xs leading-6 text-[#544835]">
              {JSON.stringify(parsedIntent, null, 2)}
            </pre>
          </details>
        </section>
      )}


      {constraintReport?.active && (
        <section className="mb-6 rounded-3xl border border-[#BDB76B]/70 bg-[#BDB76B]/14 p-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <h3 className="font-display text-2xl font-semibold text-[#4F542B]">
                Exact Constraints Enforced
              </h3>

              <p className="mt-1 text-sm text-[#706453]">
                Every returned movie passed the structured metadata checks.
              </p>
            </div>

            <span className="w-fit rounded-full border border-[#BDB76B] bg-[#FFFDF0]/65 px-3 py-1 text-xs font-semibold text-[#5E5A31]">
              {constraintReport.valid_candidate_count} valid candidates
            </span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {constraintReport.descriptions.map(
              (description) => (
                <span
                  key={description}
                  className="rounded-full border border-[#BDB76B]/70 bg-[#FFFDF0]/65 px-3 py-1 text-xs text-[#625845]"
                >
                  {description}
                </span>
              )
            )}
          </div>

          {constraintReport.result_shortfall > 0 && (
            <div className="mt-4 rounded-2xl border border-[#D4AF37]/60 bg-[#D4AF37]/12 p-4">
              <p className="font-semibold text-[#6A550F]">
                Fewer strict matches were found
              </p>

              <p className="mt-1 text-sm leading-6 text-[#625845]">
                You requested{" "}
                {constraintReport.requested_top_k} movies,
                but only{" "}
                {constraintReport.valid_candidate_count}{" "}
                candidates satisfied every hard constraint.
                Invalid movies were not added to fill the list.
              </p>
            </div>
          )}

          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-semibold text-[#626633]">
              Show constraint debug details
            </summary>

            <pre className="mt-3 overflow-x-auto rounded-2xl border border-[#BDB76B]/60 bg-[#F5EDC5] p-4 text-xs leading-6 text-[#544835]">
              {JSON.stringify(
                constraintReport,
                null,
                2
              )}
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
