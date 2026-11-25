import type { 
  RecommendRequest, 
  RecommendResponse, 
  FeedbackRequest, 
  UserMoviePreferenceResponse,
  UserMemorySummary,
  MovieSearchResponse,
  MovieReview,
 } from "@/types/movie";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const REVIEWS_URL = `${API_BASE_URL}/users/demo_user/reviews`;

export async function getReviews(signal: AbortSignal): Promise<MovieReview[]> {
  const response = await fetch(REVIEWS_URL, { signal, cache: "no-store" });
  if (!response.ok) throw new Error("Could not load your reviews.");
  return response.json();
}

export async function saveReview(
  movieId: string,
  review: Pick<MovieReview, "title" | "rating" | "body">,
): Promise<MovieReview> {
  const response = await fetch(`${REVIEWS_URL}/${encodeURIComponent(movieId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });
  if (!response.ok) throw new Error("Could not save your review. Please try again.");
  return response.json();
}

export type HealthResponse = {
  status: string;
  app_name: string;
  version: string;
  environment: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.status}`);
  }

  return response.json();
}

export async function recommendMovies(
  requestBody: RecommendRequest
): Promise<RecommendResponse> {
  const response = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    let errorMessage = `Recommendation request failed: ${response.status}`;

    try {
      const errorBody = await response.json();
      if (errorBody.detail) {
        errorMessage = Array.isArray(errorBody.detail)
        ? JSON.stringify(errorBody.detail)
        : String(errorBody.detail);
      }
    } catch {
      // Ignore JSON parsing errors and use the default error message
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

export async function searchMoviesByTitle(
  title: string,
  limit = 20,
  offset = 0,
  signal?: AbortSignal
): Promise<MovieSearchResponse> {
  const searchParams = new URLSearchParams({
    q: title,
    limit: String(limit),
    offset: String(offset),
  });
  const response = await fetch(
    `${API_BASE_URL}/movies/search?${searchParams.toString()}`,
    {
      method: "GET",
      cache: "no-store",
      signal,
    }
  );

  if (!response.ok) {
    let errorMessage = `Movie search request failed: ${response.status}`;

    try {
      const errorBody = await response.json();
      if (errorBody.detail) {
        errorMessage = Array.isArray(errorBody.detail)
          ? JSON.stringify(errorBody.detail)
          : String(errorBody.detail);
      }
    } catch {
      // Ignore JSON parsing errors and use the default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

export async function sendFeedback(
  requestBody: FeedbackRequest
): Promise<UserMoviePreferenceResponse> {
  const response = await fetch(`${API_BASE_URL}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    let errorMessage = `Feedback request failed: ${response.status}`;
    try {
      const errorBody = await response.json();
      if (errorBody.detail) {
        errorMessage = Array.isArray(errorBody.detail)
          ? JSON.stringify(errorBody.detail)
          : String(errorBody.detail);
      }
    } catch {
      // Ignore JSON parsing errors and use the default error message
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function getUserMemorySummary(
  user_id: string
): Promise<UserMemorySummary> {
  const response = await fetch(`${API_BASE_URL}/feedback/${user_id}/summary`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`User memory summary request failed: ${response.status}`);
  }

  return response.json();
}
