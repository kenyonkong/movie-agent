"use client";

import { useState} from "react";
import { RecommendationList } from "@/components/RecommendationList";
import { SearchBar } from "@/components/SearchBar";
import { recommendMovies, getUserMemorySummary } from "@/lib/api";
import type { 
  MovieRecommendation,
  UserMoviePreferenceResponse,
  UserMemorySummary,
 } from "@/types/movie";

const DEMO_USER_ID = "demo_user";

export default function Home() {
  const [query, setQuery] = useState(
    "I want something like Her, lonely and futuristic, but not too slow"
  );
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
        top_k: topK,
      });
      // setClientLatencyMs(performance.now() - startTime);

      setResults(resonse.results);
      setLatencyMs(resonse.latency_ms);
      setLastQuery(trimmedQuery);
    } catch (err) {
      setResults([]);
      setLatencyMs(null);
      setLastQuery(null);
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
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto max-w-5xl px-6 py-10 md:py-16">
        <div className="mb-8">
          <p className="mb-2 text-sm font-medium uppercase tracking-[0.3em] text-cyan-400">
            Movie Agent
          </p>
          <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
            Semantic Movie Recommendations
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-slate-400 md:text-lg">
            This is the first full-stack version of the project: a Next.js UI
            calling a FastAPI backend that retrieves movie candidates from a
            Chroma vector database.
          </p>
        </div>

        {memorySummary && (
          <section className="mb-8 rounded-3xl border border-slate-800 bg-slate-900/70 p-5">
            <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-100">
                  User Memory
                </h2>
                <p className="text-sm text-slate-400">
                  Feedback stored for {memorySummary.user_id}
                </p>
              </div>
              <p className="rounded-full border border-slate-700 px-3 py-2 text-sm text-slate-300">
                {memorySummary.total_preferences} movie preferences states
              </p>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                <p className="mb-2 text-sm font-semibold text-cyan-300">
                  Liked genres
                </p>
                <p className="text-sm text-slate-400">
                  {Object.keys(memorySummary.liked_genres).length > 0
                    ? Object.entries(memorySummary.liked_genres)
                        .map(([genre, count]) => `${genre} (${count})`)
                        .join(", ")
                    : "No liked genres yet."}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                <p className="mb-2 text-sm font-semibold text-red-300">
                  Disliked genres
                </p>
                <p className="text-sm text-slate-400">
                  {Object.keys(memorySummary.disliked_genres).length > 0
                    ? Object.entries(memorySummary.disliked_genres)
                        .map(([genre, count]) => `${genre} (${count})`)
                        .join(", ")
                    : "No disliked genres yet."}
                </p>
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                <p className="mb-2 text-sm font-semibold text-purple-300">
                  Watched movies
                </p>
                <p className="text-sm text-slate-400">
                  {memorySummary.watched_movies.length > 0
                    ? memorySummary.watched_movies.join(", ")
                    : "No watched movies yet."}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                <p className="mb-2 text-sm font-semibold text-yellow-300">
                  Saved movies
                </p>
                <p className="text-sm text-slate-400">
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
          isLoading={isLoading}
          onQueryChange={setQuery}
          onTopKChange={setTopK}
          onSubmit={handleRecommend}
        />

        {error && (
          <div className="mt-6 rounded-2xl border border-red-900/70 bg-red-950/40 p-4 text-sm text-red-200">
            <p className="font-semibold">Something went wrong</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="mt-8 rounded-3xl border border-slate-800 bg-slate-900/80 p-6 text-slate-300">
            Searching your movie vector database...
          </div>
        )}

        {lastQuery && !isLoading && (
          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
            <span className="font-semibold text-slate-100">Last query:</span>{" "}
            {lastQuery}
          </div>
        )}

        {!isLoading && !lastQuery && results.length === 0 && (
          <div className="mt-8 rounded-3xl border border-dashed border-slate-700 bg-slate-900/40 p-8 text-center">
            <p className="text-lg font-semibold text-slate-200">
              Start with a natural-language movie mood.
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Try describing a reference movie, emotion, genre, pacing, or theme.
            </p>
          </div>
        )}

        {!isLoading && (
          <RecommendationList
          results={results}
          latencyMs={latencyMs}
          userId={DEMO_USER_ID}
          query={lastQuery}
          onPreferenceSaved={handlePreferenceSaved}
          />
        )}
      </section>
    </main>
  );
}
