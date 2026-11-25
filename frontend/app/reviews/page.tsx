"use client";

import Link from "next/link";
import Image from "next/image";
import { MovieReviewPanel } from "@/components/MovieReviewPanel";
import { useReviews } from "@/components/ReviewsProvider";

export default function ReviewsPage() {
  const { reviews, loading, error, retry } = useReviews();

  return (
    <main className="app-page">
      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="page-hero rounded-[2.25rem] px-6 py-10 md:px-10 md:py-14">
          <h1 className="font-display text-4xl font-semibold md:text-6xl">My Reviews</h1>
          <p className="mt-3 text-[#706453]">Most recently updated first.</p>
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
          {reviews.map((review) => (
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
                <time dateTime={review.updated_at} className="mb-4 block text-sm text-[#706453]">
                  Updated {new Date(review.updated_at).toLocaleString()}
                </time>
                <MovieReviewPanel movieId={review.movie_id} title={review.title} review={review} />
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
