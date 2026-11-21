"use client";

import { useState } from "react";
import { RecommendationList } from "@/components/RecommendationList";
import { SearchBar } from "@/components/SearchBar";
import { recommendMovies, getUserMemorySummary } from "@/lib/api";
import type { 
  MovieIntent,
  MovieRecommendation,
  UserMoviePreferenceResponse,
  UserMemorySummary,
  AgentTrace,
  ConstraintReport,
 } from "@/types/movie";

const DEMO_USER_ID = "demo_user";

export default function Home() {
  const [query, setQuery] = useState(
    "I want something like Her, lonely and futuristic, but not too slow"
  );

  const [includeWatched, setIncludeWatched] = useState(false);
  const [candidateCount, setCandidateCount] = useState<number | null>(null);
  const [filteredWatchedCount, setFilteredWatchedCount] = useState<number | null>(null);

  const [useLlmIntent, setUseLlmIntent] = useState(false);
  const [intentProvider, setIntentProvider] = useState<string | null>(null);
  const [retrievalQuery, setRetrievalQuery] = useState<string | null>(null);
  const [parsedIntent, setParsedIntent] = useState<MovieIntent | null>(null);

  const [enforceHardConstraints, setEnforceHardConstraints] = useState(true);
  const [constraintReport, setConstraintReport] = useState<ConstraintReport | null>(null);

  const [useLlmExplanations, setUseLlmExplanations] = useState(false);
  const [explanationProvider, setExplanationProvider] = useState<string | null>(
    null
  );
  const [useLlmReranker, setUseLlmReranker] = useState(false);
  const [rerankerProvider, setRerankerProvider] = useState<string | null>(null);
  const [rerankerFallbackUsed, setRerankerFallbackUsed] = useState<boolean | null>(null);

  const [includeAgentTrace, setIncludeAgentTrace] = useState(true);
  const [agentTrace, setAgentTrace] = useState<AgentTrace | null>(null);

  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState<MovieRecommendation[]>([]);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // const [clientLatencyMs, setClientLatencyMs] = useState<number | null>(null);
  const [memorySummary, setMemorySummary] = useState<UserMemorySummary | null>(null);

  async function refreshMemorySummary() {
    try {
      const summary = await getUserMemorySummary(DEMO_USER_ID);
      setMemorySummary(summary);
    } catch {
        // Memory summary is helpful but should not break the main UX.
    }
  }

  async function handleRecommend() {
    const trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      setError("Please enter a more detailed movie preference.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      // const startTime = performance.now();
      const resonse = await recommendMovies({ 
        user_id: "demo_user",
        query: trimmedQuery,
        include_watched: includeWatched,
        top_k: topK,
        use_llm_explanations: useLlmExplanations,
        use_llm_intent: useLlmIntent,
        enforce_hard_constraints: enforceHardConstraints,
        use_llm_reranker: useLlmReranker,
        include_agent_trace: includeAgentTrace,
      });
      // setClientLatencyMs(performance.now() - startTime);

      setResults(resonse.results);
      setLatencyMs(resonse.latency_ms);
      setCandidateCount(resonse.candidate_count);
      setFilteredWatchedCount(resonse.filtered_watched_count);
      setIntentProvider(resonse.intent_provider);
      setRetrievalQuery(resonse.retrieval_query);
      setParsedIntent(resonse.parsed_intent);
      setConstraintReport(resonse.constraint_report);
      setExplanationProvider(resonse.explanation_provider);
      setRerankerProvider(resonse.reranker_provider);
      setRerankerFallbackUsed(resonse.reranker_fallback_used);
      setAgentTrace(resonse.agent_trace);
      setLastQuery(trimmedQuery);
    } catch (err) {
      setResults([]);
      setLatencyMs(null);
      setCandidateCount(null);
      setFilteredWatchedCount(null);
      setIntentProvider(null);
      setRetrievalQuery(null);
      setParsedIntent(null);
      setConstraintReport(null);
      setExplanationProvider(null);
      setRerankerProvider(null);
      setRerankerFallbackUsed(null);
      setLastQuery(null);
      setAgentTrace(null);
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setIsLoading(false);
    }
  }
  
  async function handlePreferenceSaved(
    preferenceState: UserMoviePreferenceResponse
  ) {
    setResults((currentResults) =>
      currentResults.map((movie) =>
        movie.movie_id === preferenceState.movie_id
          ? {
              ...movie,
              preference: preferenceState.preference,
              watched: preferenceState.watched,
              saved: preferenceState.saved,
            }
          : movie
      )
    );

    await refreshMemorySummary();
  }

  return (
    <main className="app-page">
      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="page-hero mb-8 rounded-[2.25rem] px-6 py-10 md:px-10 md:py-14">
          <p className="eyebrow mb-3">Thoughtful movie discovery</p>
          <h1 className="font-display max-w-4xl text-4xl font-semibold leading-[1.05] text-[#352D22] md:text-6xl lg:text-7xl">
            Find the movie that fits the moment.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[#706453] md:text-lg">
            Describe what you want to feel, and Movie Agent will search the
            catalog for grounded, personal recommendations with reasons you can
            trust.
          </p>
        </div>

        {memorySummary && (
          <section className="surface-card mb-8 rounded-3xl p-5">
            <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="font-display text-2xl font-semibold text-[#352D22]">
                  User Memory
                </h2>
                <p className="text-sm text-[#706453]">
                  Feedback stored for {memorySummary.user_id}
                </p>
              </div>
              <p className="rounded-full border border-[#BDB76B]/70 bg-[#FDFBD4]/70 px-3 py-2 text-sm text-[#544835]">
                {memorySummary.total_preferences} movie preference states
              </p>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
                <p className="mb-2 text-sm font-semibold text-[#826714]">
                  Liked genres
                </p>
                <p className="text-sm text-[#706453]">
                  {Object.keys(memorySummary.liked_genres).length > 0
                    ? Object.entries(memorySummary.liked_genres)
                        .map(([genre, count]) => `${genre} (${count})`)
                        .join(", ")
                    : "No liked genres yet."}
                </p>
              </div>

              <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
                <p className="mb-2 text-sm font-semibold text-[#9A592E]">
                  Disliked genres
                </p>
                <p className="text-sm text-[#706453]">
                  {Object.keys(memorySummary.disliked_genres).length > 0
                    ? Object.entries(memorySummary.disliked_genres)
                        .map(([genre, count]) => `${genre} (${count})`)
                        .join(", ")
                    : "No disliked genres yet."}
                </p>
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
                <p className="mb-2 text-sm font-semibold text-[#6D6940]">
                  Watched movies
                </p>
                <p className="text-sm text-[#706453]">
                  {memorySummary.watched_movies.length > 0
                    ? memorySummary.watched_movies.join(", ")
                    : "No watched movies yet."}
                </p>
              </div>

              <div className="rounded-2xl border border-[#BDB76B]/50 bg-[#FDFBD4]/55 p-4">
                <p className="mb-2 text-sm font-semibold text-[#826714]">
                  Saved movies
                </p>
                <p className="text-sm text-[#706453]">
                  {memorySummary.saved_movies.length > 0
                    ? memorySummary.saved_movies.join(", ")
                    : "No saved movies yet."}
                </p>
              </div>
            </div>
          </section>
        )}


        <SearchBar
          query={query}
          topK={topK}
          includeWatched={includeWatched}
          useLlmExplanations={useLlmExplanations}
          useLlmIntent={useLlmIntent}
          enforceHardConstraints={enforceHardConstraints}
          useLlmReranker={useLlmReranker}
          includeAgentTrace={includeAgentTrace}
          isLoading={isLoading}
          onQueryChange={setQuery}
          onTopKChange={setTopK}
          onIncludeWatchedChange={setIncludeWatched}
          onUseLlmExplanationsChange={setUseLlmExplanations}
          onUseLlmIntentChange={setUseLlmIntent}
          onEnforceHardConstraintsChange={setEnforceHardConstraints}
          onUseLlmRerankerChange={setUseLlmReranker}
          onIncludeAgentTraceChange={setIncludeAgentTrace}
          onSubmit={handleRecommend}
        />

        {error && (
          <div className="mt-6 rounded-2xl border border-[#B86B4B]/55 bg-[#FFF2DF] p-4 text-sm text-[#764025] shadow-sm">
            <p className="font-semibold">We could not find recommendations</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="surface-card mt-8 rounded-3xl p-6 text-[#625845]">
            <p className="font-display text-xl text-[#352D22]">
              Curating your recommendations...
            </p>
            <p className="mt-1 text-sm text-[#706453]">
              Searching the catalog and ranking the strongest matches.
            </p>
          </div>
        )}

        {lastQuery && !isLoading && (
          <div className="mt-6 rounded-2xl border border-[#BDB76B]/55 bg-[#FFFDF0]/65 p-4 text-sm text-[#625845]">
            <span className="font-semibold text-[#352D22]">Your request:</span>{" "}
            {lastQuery}
          </div>
        )}

        {!isLoading && !lastQuery && results.length === 0 && (
          <div className="empty-state mt-8 rounded-3xl p-8 text-center">
            <p className="font-display text-2xl font-semibold text-[#352D22]">
              Start with a natural-language movie mood.
            </p>
            <p className="mt-2 text-sm text-[#706453]">
              Try describing a reference movie, emotion, genre, pacing, or theme.
            </p>
          </div>
        )}

        {!isLoading && (
          <RecommendationList
          agentTrace={agentTrace}
          results={results}
          latencyMs={latencyMs}
          candidateCount={candidateCount}
          filteredWatchedCount={filteredWatchedCount}
          includeWatched={includeWatched}
          rerankerProvider={rerankerProvider}
          rerankerFallbackUsed={rerankerFallbackUsed}
          explanationProvider={explanationProvider}
          intentProvider={intentProvider}
          retrievalQuery={retrievalQuery}
          parsedIntent={parsedIntent}
          userId={DEMO_USER_ID}
          query={lastQuery}
          constraintReport={constraintReport}
          onPreferenceSaved={handlePreferenceSaved}
          />
        )}
      </section>
    </main>
  );
}
