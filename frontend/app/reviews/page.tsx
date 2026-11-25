"use client";

import Link from "next/link";
import Image from "next/image";
import { useRef, useState } from "react";
import { MovieReviewPanel } from "@/components/MovieReviewPanel";
import { useReviews } from "@/components/ReviewsProvider";

const PAGE_SIZE = 10;

export default function ReviewsPage() {
  const { reviews, loading, error, retry } = useReviews();
  const [selectedPage, setSelectedPage] = useState(1);
  const heading = useRef<HTMLHeadingElement>(null);
  const pageCount = Math.max(1, Math.ceil(reviews.length / PAGE_SIZE));
  const page = Math.min(selectedPage, pageCount);
  const start = (page - 1) * PAGE_SIZE;
  const pageNumbers = [...new Set([1, page - 1, page, page + 1, pageCount])]
    .filter((number) => number >= 1 && number <= pageCount)
    .sort((a, b) => a - b);

  function goToPage(number: number) {
    if (number === page || number < 1 || number > pageCount) return;
    setSelectedPage(number);
    heading.current?.focus();
    heading.current?.scrollIntoView({ block: "center" });
  }

  return (
    <main className="app-page">
      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="page-hero rounded-[2.25rem] px-6 py-10 md:px-10 md:py-14">
          <h1 ref={heading} tabIndex={-1} className="font-display text-4xl font-semibold md:text-6xl">My Reviews</h1>
          <p className="mt-3 text-[#706453]">Newest reviews first by review date.</p>
        </div>

        {loading && <p role="status" className="mt-8">Loading your reviews…</p>}
        {error && (
          <div className="mt-8 space-y-3">
            <p role="alert">{error}</p>
            <button type="button" onClick={retry} className="secondary-action rounded-full px-4 py-2">Try again</button>
          </div>
        )}
        {!loading && !error && reviews.length === 0 && (
          <div className="empty-state mt-8 space-y-4 rounded-3xl p-6">
            <p>Find a movie to write your first review.</p>
            <Link href="/movies" className="primary-action inline-block rounded-full px-5 py-2">Browse movies</Link>
          </div>
        )}
        <div className="mt-8 space-y-4">
          {reviews.slice(start, start + PAGE_SIZE).map((review) => (
            <article key={review.movie_id} className="surface-card flex flex-col items-start gap-5 rounded-3xl p-6 sm:flex-row">
              <div className="relative flex aspect-[2/3] w-32 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-[#F5EDC5] sm:w-40">
                {review.poster_url ? (
                  <Image
                    src={review.poster_url}
                    alt={`${review.title} poster`}
                    fill
                    sizes="(min-width: 640px) 160px, 128px"
                    className="object-cover"
                  />
                ) : (
                  <span className="px-2 text-center text-sm text-[#706453]">No poster available</span>
                )}
              </div>
              <div className="w-full min-w-0 flex-1">
                <h2 className="font-display break-words text-3xl">{review.title}</h2>
                <time dateTime={review.marked_date ?? review.updated_at} className="mb-4 block text-sm text-[#706453]">
                  {review.marked_date
                    ? new Date(review.marked_date).toLocaleDateString(undefined, { timeZone: "UTC" })
                    : new Date(review.updated_at).toLocaleString()}
                </time>
                <MovieReviewPanel movieId={review.movie_id} title={review.title} review={review} />
              </div>
            </article>
          ))}
        </div>
        {!loading && !error && pageCount > 1 && (
          <nav aria-label="Review pages" className="mt-8 space-y-3 text-center">
            <p role="status" className="text-sm text-[#706453]">Page {page} of {pageCount}</p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                aria-label="Previous page"
                disabled={page === 1}
                onClick={() => goToPage(page - 1)}
                className="secondary-action min-h-10 min-w-10 rounded-full disabled:opacity-40"
              >
                ←
              </button>
              {pageNumbers.map((number, index) => (
                <div key={number} className="flex items-center gap-2">
                  {index > 0 && number - pageNumbers[index - 1] > 1 && (
                    <span aria-hidden="true">…</span>
                  )}
                  <button
                    type="button"
                    aria-label={`Page ${number}`}
                    aria-current={number === page ? "page" : undefined}
                    onClick={() => goToPage(number)}
                    className={`min-h-10 min-w-10 rounded-full ${number === page ? "primary-action" : "secondary-action"}`}
                  >
                    {number}
                  </button>
                </div>
              ))}
              <button
                type="button"
                aria-label="Next page"
                disabled={page === pageCount}
                onClick={() => goToPage(page + 1)}
                className="secondary-action min-h-10 min-w-10 rounded-full disabled:opacity-40"
              >
                →
              </button>
            </div>
          </nav>
        )}
      </section>
    </main>
  );
}
