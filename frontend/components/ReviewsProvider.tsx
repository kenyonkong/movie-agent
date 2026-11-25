"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getReviews } from "@/lib/api";
import type { MovieReview } from "@/types/movie";

const ReviewsContext = createContext<{
  reviews: MovieReview[];
  loading: boolean;
  error: string | null;
  retry: () => void;
  update: (review: MovieReview) => void;
} | null>(null);

export function ReviewsProvider({ children }: { children: ReactNode }) {
  const [reviews, setReviews] = useState<MovieReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getReviews(controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) setReviews(items);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError("Could not load your reviews.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt]);

  function retry() {
    setError(null);
    setLoading(true);
    setAttempt((current) => current + 1);
  }

  function update(review: MovieReview) {
    setReviews((current) =>
      [review, ...current.filter((item) => item.movie_id !== review.movie_id)]
        .sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at)),
    );
  }

  return (
    <ReviewsContext.Provider value={{ reviews, loading, error, retry, update }}>
      {children}
    </ReviewsContext.Provider>
  );
}

export function useReviews() {
  const context = useContext(ReviewsContext);
  if (!context) throw new Error("ReviewsProvider is required.");
  return context;
}
