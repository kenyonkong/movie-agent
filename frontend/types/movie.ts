export type MovieRecommendation = {
    movie_id: string;
    title: string;
    release_year: number | null;
    genres: string | null;
    score: number;
    distance: number;
    reason: string;
    document_preview: string;
};

export type RecommendRequest = {
    user_id: string;
    query: string;
    top_k: number;
};

export type RecommendResponse = {
    user_id: string;
    query: string;
    top_k: number;
    results: MovieRecommendation[];
    latency_ms: number;
};

export type FeedbackAction = 'like' | 'dislike' | 'watched' | 'save';

export type FeedbackRequest = {
    user_id: string;
    movie_id: string;
    title: string;
    action: FeedbackAction;
    query?: string| null;
    genres?: string | null;
    score?: number | null;
};

export type FeedbackResponse = {
    id: number;
    user_id: string;
    movie_id: string;
    title: string;
    action: FeedbackAction;
    query: string | null;
    genres: string | null;
    score: number | null;
    created_at: string;
};

export type UserMemorySummary = {
    user_id: string;
    total_feedback: number;
    liked_movies: string[];
    disliked_movies: string[];
    watched_movies: string[];
    saved_movies: string[];
    liked_genres: Record<string, number>;
    disliked_genres: Record<string, number>;
};
