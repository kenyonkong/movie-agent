import type { 
  RecommendRequest, 
  RecommendResponse, 
  FeedbackRequest, 
  FeedbackResponse, 
  UserMemorySummary
 } from "@/types/movie";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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

export async function sendFeedback(
  requestBody: FeedbackRequest
): Promise<FeedbackResponse> {
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
