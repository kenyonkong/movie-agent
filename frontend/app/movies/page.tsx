"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { BrowseMovieCard } from "@/components/BrowseMovieCard";
import { searchMoviesByTitle } from "@/lib/api";
import type { MovieSearchItem } from "@/types/movie";

const PAGE_SIZE = 12;

export default function BrowseMoviesPage() {
  const [query, setQuery] = useState("");
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [results, setResults] = useState<MovieSearchItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(title: string, nextOffset: number) {
    try {
      setIsLoading(true);
      setError(null);

      const response = await searchMoviesByTitle(
        title,
        PAGE_SIZE,
        nextOffset
      );

      setResults(response.results);
      setTotal(response.total);
      setOffset(response.offset);
      setLastQuery(response.query);
    } catch (searchError) {
      setResults([]);
      setTotal(0);
      setOffset(0);
      setError(
        searchError instanceof Error
          ? searchError.message
          : "An unknown error occurred."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setError("Enter a movie title to search.");
      return;
    }

    void runSearch(trimmedQuery, 0);
  }

  function goToPage(nextOffset: number) {
    if (lastQuery) {
      void runSearch(lastQuery, nextOffset);
    }
  }

  const firstResult = total === 0 ? 0 : offset + 1;
  const lastResult = Math.min(offset + results.length, total);

  return (
    <main className="app-page">
      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="page-hero mb-8 rounded-[2.25rem] px-6 py-10 md:px-10 md:py-14">
          <p className="eyebrow mb-3">Browse Movies</p>
          <h1 className="font-display max-w-4xl text-4xl font-semibold leading-[1.05] text-[#352D22] md:text-6xl">
            Search the catalog by title.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[#706453] md:text-lg">
            Find a familiar favorite or something you have been meaning to see.
            Matches are ordered by current catalog popularity.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="surface-card rounded-[2rem] p-5 md:p-7"
        >
          <label
            htmlFor="movie-title-search"
            className="text-sm font-semibold text-[#544835]"
          >
            Movie title
          </label>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input
              id="movie-title-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Try Batman, Parasite, or Spirited Away"
              autoComplete="off"
              className="warm-field min-w-0 flex-1 rounded-xl px-4 py-3 outline-none transition"
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="primary-action rounded-full px-7 py-3 font-bold transition disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? "Searching..." : "Search movies"}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 rounded-2xl border border-[#B86B4B]/55 bg-[#FFF2DF] p-4 text-sm text-[#764025] shadow-sm">
            <p className="font-semibold">Movie search failed</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="surface-card mt-8 rounded-3xl p-6 text-[#625845]">
            <p className="font-display text-xl text-[#352D22]">
              Searching the shelves...
            </p>
            <p className="mt-1 text-sm text-[#706453]">
              Looking for matching titles in the movie catalog.
            </p>
          </div>
        )}

        {!isLoading && lastQuery && !error && (
          <div className="mt-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-display text-3xl font-semibold text-[#352D22]">
                Results for “{lastQuery}”
              </h2>
              <p className="mt-1 text-sm text-[#706453]">
                {total === 0
                  ? "No matching titles found."
                  : `Showing ${firstResult}–${lastResult} of ${total} matches, sorted by popularity.`}
              </p>
            </div>
          </div>
        )}

        {!isLoading && results.length > 0 && (
          <div className="mt-6 grid gap-6">
            {results.map((movie, index) => (
              <BrowseMovieCard
                key={movie.movie_id}
                movie={movie}
                priority={index < 2}
              />
            ))}
          </div>
        )}

        {!isLoading && lastQuery && total > PAGE_SIZE && (
          <div className="mt-8 flex items-center justify-between gap-4">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => goToPage(Math.max(0, offset - PAGE_SIZE))}
              className="secondary-action rounded-full px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={offset + results.length >= total}
              onClick={() => goToPage(offset + PAGE_SIZE)}
              className="secondary-action rounded-full px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}

        {!isLoading && !lastQuery && (
          <div className="empty-state mt-8 rounded-3xl p-8 text-center">
            <p className="font-display text-2xl font-semibold text-[#352D22]">
              Start with a movie title.
            </p>
            <p className="mt-2 text-sm text-[#706453]">
              Results will include the year, director, cast, rating, poster, and
              backdrop when available.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
