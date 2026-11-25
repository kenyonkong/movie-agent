"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useReviews } from "@/components/ReviewsProvider";
import { saveReview } from "@/lib/api";
import type { MovieReview } from "@/types/movie";

const STARS = [1, 2, 3, 4, 5];

function Star({ filled }: { filled: boolean }) {
  return (
    <span aria-hidden="true" className={filled ? "text-[#947215]" : "text-[#BDB76B]"}>
      {filled ? "★" : "☆"}
    </span>
  );
}

function ReviewEditor({ movieId, title, review, onClose }: {
  movieId: string;
  title: string;
  review?: MovieReview;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useId();
  const { update } = useReviews();
  const [rating, setRating] = useState(review?.rating ?? 0);
  const [body, setBody] = useState(review?.body ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || !rating || !body.trim()) return;
    setSaving(true);
    setError(null);
    try {
      update(await saveReview(movieId, { title, rating, body: body.trim() }));
      onClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not save your review.");
      setSaving(false);
    }
  }

  return (
    <dialog
      ref={dialog}
      aria-labelledby={heading}
      onCancel={(event) => {
        event.preventDefault();
        if (!saving) onClose();
      }}
      className="surface-card fixed inset-0 m-auto max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-lg overflow-y-auto rounded-3xl p-6 text-[#352D22] backdrop:bg-[#352D22]/45"
    >
      <form onSubmit={submit} className="space-y-5">
        <h2 id={heading} className="font-display text-2xl">
          {review ? "Edit review" : "Write a review"} for {title}
        </h2>
        <fieldset disabled={saving} className="space-y-2">
          <legend className="font-semibold">Your rating (required)</legend>
          <div className="flex w-fit text-4xl leading-none">
            {STARS.map((star) => (
              <label key={star} className="cursor-pointer rounded-sm px-0.5 focus-within:ring-2 focus-within:ring-[#947215]">
                <input
                  className="sr-only"
                  type="radio"
                  name="rating"
                  value={star}
                  checked={rating === star}
                  onChange={() => setRating(star)}
                  aria-label={`${star} out of 5 stars`}
                  required
                />
                <Star filled={star <= rating} />
              </label>
            ))}
          </div>
        </fieldset>
        <label className="block font-semibold">
          Your review
          <textarea
            className="warm-field mt-2 block min-h-32 w-full rounded-xl p-3 font-normal"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            disabled={!rating || saving}
            maxLength={5000}
            required
          />
        </label>
        {error && <p role="alert" className="text-[#814526]">{error}</p>}
        <div className="flex flex-wrap justify-end gap-3">
          <button type="button" onClick={onClose} disabled={saving} className="secondary-action rounded-full px-4 py-2">Cancel</button>
          <button type="submit" disabled={saving || !rating || !body.trim()} className="primary-action rounded-full px-4 py-2 disabled:opacity-50">
            {saving ? "Saving…" : "Save review"}
          </button>
        </div>
      </form>
    </dialog>
  );
}

export function MovieReviewPanel({ movieId, title, review }: {
  movieId: string;
  title: string;
  review?: MovieReview;
}) {
  const { reviews, loading, error, retry } = useReviews();
  const [editing, setEditing] = useState(false);
  const current = review ?? reviews.find((item) => item.movie_id === movieId);

  if (loading) return <p role="status" className="text-sm">Loading review…</p>;
  if (error) {
    return <button type="button" className="secondary-action rounded-full px-4 py-2" onClick={retry}>Retry loading reviews</button>;
  }

  return (
    <section className="space-y-3">
      {current && (
        <div className="rounded-xl border border-[#BDB76B]/60 bg-[#FFFDF0] p-4">
          <p className="text-sm font-semibold">Your review</p>
          <p className="flex items-center gap-2">
            <span className="text-2xl" aria-hidden="true">
              {STARS.map((star) => (
                <Star key={star} filled={star <= current.rating} />
              ))}
            </span>
            <span className="sr-only">{current.rating} out of 5 stars</span>
          </p>
          <p className="mt-2 whitespace-pre-wrap break-words" lang={current.review_en ? "en" : undefined}>
            {current.review_en ?? current.body}
          </p>
        </div>
      )}
      <button type="button" onClick={() => setEditing(true)} className="secondary-action rounded-full px-4 py-2 text-sm font-semibold">
        {current ? "Edit review" : "Write review"}
      </button>
      {editing && <ReviewEditor movieId={movieId} title={title} review={current} onClose={() => setEditing(false)} />}
    </section>
  );
}
