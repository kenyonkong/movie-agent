# API Contract

The FastAPI application serves JSON at `http://localhost:8000` by default.
Interactive OpenAPI documentation is available at `/docs`.

## Health

```http
GET /health
```

Returns application status, name, version, and environment.

## Recommend movies

```http
POST /recommend
Content-Type: application/json
```

Example request:

```json
{
  "user_id": "demo_user",
  "query": "A Korean-language thriller after 2000 under two hours",
  "top_k": 5,
  "include_watched": false,
  "use_llm_intent": false,
  "enforce_hard_constraints": true,
  "use_llm_reranker": false,
  "use_llm_explanations": false,
  "include_agent_trace": true
}
```

`top_k` must be between 1 and 10. The query must contain 2–500 characters.
LLM flags only use OpenAI when the matching backend provider is configured;
otherwise the deterministic implementation or fallback is used.

The response contains:

- Original and retrieval queries
- Parsed structured intent and intent provider
- Constraint-enforcement report
- Candidate and watched-filter counts
- Reranker and explanation provider information
- Ranked movie results with metadata, images, scores, reasons, and signals
- Total latency and an optional sanitized agent trace

The response field is named `include_watched`, matching the request contract.
When exact constraints leave fewer than `top_k` valid movies, `results` is
shorter and `constraint_report.result_shortfall` explains the difference.

## Search the movie catalog

```http
GET /movies/search?q=Batman&limit=20&offset=0
```

The endpoint performs case-insensitive substring matching against the `title`
field only and returns matches in descending TMDB popularity order. `q` must
contain 1–200 characters, `limit` must be 1–50, and `offset` must be zero or
greater.

Example response:

```json
{
  "query": "Batman",
  "total": 3,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "movie_id": "268",
      "title": "Batman",
      "release_year": 1989,
      "director": "Tim Burton",
      "cast": ["Michael Keaton", "Jack Nicholson"],
      "movie_rating": 7.2,
      "poster_url": "https://image.tmdb.org/t/p/w500/example.jpg",
      "backdrop_url": "https://image.tmdb.org/t/p/w780/example.jpg"
    }
  ]
}
```

Search does not use embeddings, feedback memory, or review data.

## Save feedback

```http
POST /feedback/
Content-Type: application/json
```

Example request:

```json
{
  "user_id": "demo_user",
  "movie_id": "152601",
  "title": "Her",
  "action": "like",
  "query": "thoughtful futuristic romance",
  "genres": "Romance, Science Fiction, Drama",
  "score": 0.82
}
```

`action` is one of `like`, `dislike`, `watched`, or `save`. Like and dislike
replace the single preference value; watched and saved are independent flags.
The endpoint upserts one current row per user/movie pair.

## Read preference state

```http
GET /feedback/{user_id}?limit=10
GET /feedback/{user_id}/summary
```

The first endpoint returns recently updated preference states. The summary
returns this shape:

```json
{
  "user_id": "demo_user",
  "total_preferences": 1,
  "liked_movies": ["Her"],
  "disliked_movies": [],
  "watched_movies": [],
  "saved_movies": [],
  "liked_genres": {
    "Romance": 1,
    "Science Fiction": 1,
    "Drama": 1
  },
  "disliked_genres": {}
}
```

## Debug configuration

```http
GET /recommend/debug
```

Returns the active vector collection, embedding configuration, intent parser,
constraint strategy, bounded reranker, and explanation provider. This endpoint
is intended for local development and should not expose secrets.
