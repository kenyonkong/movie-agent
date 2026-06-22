export type FeedbackAction = 'like' | 'dislike' | 'watched' | 'save';
export type PreferenceValue = "like" | "dislike";
export type AgentTraceStatus = "completed" | "skipped" | "failed";

export type AgentTraceStep = {
  name: string;
  status: AgentTraceStatus;
  duration_ms: number;
  details: Record<string, unknown>;
};

export type AgentTrace = {
  agent_name: string;
  agent_version: string;
  total_duration_ms: number;
  steps: AgentTraceStep[];
};

export type MovieIntent = {
  raw_query: string;
  query_rewrite: string;

  reference_movies: string[];
  moods: string[];
  themes: string[];
  genres: string[];

  pacing: string | null;
  tone: string[];

  avoid: string[];
  constraints: string[];

  confidence: number;
  parser_notes: string;
};


export type MovieRecommendation = {
    movie_id: string;
    title: string;
    release_year: number | null;
    genres: string | null;

    // TMDB image data
    poster_path: string | null;
    poster_url: string | null;
    backdrop_path: string | null;
    backdrop_url: string | null;

    score: number;
    distance: number;
    semantic_score: number;
    preference_score: number;
    novelty_score: number;
    diversity_penalty: number;

    // User preferences
    preference: PreferenceValue | null;
    watched: boolean;
    saved: boolean;

    popularity: number | null;
    vote_average: number | null;
    vote_count: number | null;

    // LLM reranker
    heuristic_rank: number | null;
    llm_rank: number | null;
    llm_rerank_reason: string | null;

    reason: string;
    document_preview: string;

    ranking_signals: Record<string, number | boolean | string>;
};

export type RecommendRequest = {
    user_id: string;
    query: string;
    top_k: number;
    include_watched: boolean;
    use_llm_explanations: boolean;
    use_llm_intent: boolean;
    use_llm_reranker: boolean;
    include_agent_trace: boolean;
};

export type RecommendResponse = {
    user_id: string;
    query: string;
    retrieval_query: string;
    parsed_intent: MovieIntent;
    intent_provider: string;

    top_k: number;
    included_watched: boolean;
    candidate_count: number;
    filtered_watched_count: number;
    explanation_provider: string;

    reranker_provider: string;
    reranker_fallback_used: boolean;

    results: MovieRecommendation[];
    latency_ms: number;
    agent_trace: AgentTrace | null;
};


export type FeedbackRequest = {
    user_id: string;
    movie_id: string;
    title: string;
    action: FeedbackAction;
    query?: string| null;
    genres?: string | null;
    score?: number | null;
};

export type UserMoviePreferenceResponse = {
    id: number;
    user_id: string;
    movie_id: string;
    title: string;

    query: string | null;
    genres: string | null;
    score: number | null;

    preference: PreferenceValue | null;
    watched: boolean;
    saved: boolean;

    created_at: string;
    updated_at: string;
};

export type UserMemorySummary = {
    user_id: string;
    total_preferences: number;

    liked_movies: string[];
    disliked_movies: string[];
    watched_movies: string[];
    saved_movies: string[];
    
    liked_genres: Record<string, number>;
    disliked_genres: Record<string, number>;
};
