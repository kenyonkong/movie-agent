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