"use client";

import { useState } from "react";
import { sendFeedback } from "@/lib/api";
import type {
    FeedbackAction,
    MovieRecommendation,
    PreferenceValue,
    UserMoviePreferenceResponse,
} from "@/types/movie";

type FeedbackButtonsProps = {
    movie: MovieRecommendation;
    userId: string;
    query: string | null;
    onFeedbackSaved?: (feedback: UserMoviePreferenceResponse) => void;
};

const ACTIONS: {
    action: FeedbackAction;
    label: string;   
}[] = [
    { action: "like", label: "Like" },
    { action: "dislike", label: "Dislike" },
    { action: "watched", label: "Watched" },
    { action: "save", label: "Save" },
];

export function FeedbackButtons({
    movie,
    userId,
    query,
    onFeedbackSaved,
}: FeedbackButtonsProps) {
    const [pendingAction, setPendingAction] = useState<FeedbackAction | null>(null);

    const [preference, setPreference] = useState<PreferenceValue | null>(null);
    const [watched, setWatched] = useState(false);
    const [saved, setSaved] = useState(false);

    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleFeedback(action: FeedbackAction) {
        try {
            setPendingAction(action);
            setError(null);
            setStatusMessage(null);

            const response = await sendFeedback({
                user_id: userId,
                movie_id: movie.movie_id,
                title: movie.title,
                action,
                query,
                genres: movie.genres,
                score: movie.score,
            });

            setPreference(response.preference);
            setWatched(response.watched);
            setSaved(response.saved);

            setStatusMessage(
              `Saved state: preference=${response.preference ?? "none"}, watched=${
                response.watched
              }, saved=${response.saved}`
            );

            onFeedbackSaved?.(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save feedback");
        } finally {
            setPendingAction(null);
        }
    }

    function isActionActive(action: FeedbackAction): boolean {
      if (action === "like") {
        return preference === "like";
      }

      if (action === "dislike") {
        return preference === "dislike";
      }

      if (action === "watched") {
        return watched;
      }

      if (action === "save") {
        return saved;
      }

      return false;
    }

    return (
    <div className="mt-5">
      <div className="flex flex-wrap gap-2">
        {ACTIONS.map(({ action, label }) => {
          const isPending = pendingAction === action;
          const isActive = isActionActive(action);

          return (
            <button
              key={action}
              type="button"
              onClick={() => handleFeedback(action)}
              disabled={pendingAction !== null}
              className={[
                "rounded-full border px-3 py-2 text-xs transition disabled:cursor-not-allowed disabled:opacity-60",
                isActive
                  ? "border-cyan-400 bg-cyan-400/10 text-cyan-300"
                  : "border-slate-700 text-slate-300 hover:border-cyan-400 hover:text-cyan-300",
              ].join(" ")}
            >
              {isPending ? "Saving..." : label}
            </button>
          );
        })}
      </div>

      {statusMessage && <p className="mt-2 text-xs text-green-300">{statusMessage}</p>}

      {error && <p className="mt-2 text-xs text-red-300">{error}</p>}
    </div>
  );
}