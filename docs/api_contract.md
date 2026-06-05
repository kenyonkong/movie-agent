# API Contract

## Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "app_name": "Movie Agent API",
  "version": "0.1.0",
  "environment": "development"
}
```

## Recommend Movies

```http
POST /recommend
```

Example request:

```json
{
  "user_id": "demo_user",
  "query": "I want something like Her, lonely and futuristic, but not too slow",
  "top_k": 5,
  "include_watched": false
}
```

Example response:

```json
{
  "user_id": "demo_user",
  "query": "I want something like Her, lonely and futuristic, but not too slow",
  "top_k": 5,
  "include_watched": false,
  "candidate_count": 40,
  "filtered_watched_count": 1,
  "results": [
    {
      "movie_id": "123",
      "title": "After Yang",
      "release_year": 2021,
      "genres": "Science Fiction, Drama",
      "score": 0.52,
      "distance": 0.96,
      "semantic_score": 0.51,
      "preference_score": 0.33,
      "preference": null,
      "watched": false,
      "saved": false,
      "reason": "After Yang was retrieved because...",
      "document_preview": "Title: After Yang...",
      "ranking_signals": {
        "semantic_score": 0.51,
        "preference_score": 0.33,
        "saved_boost": 0.0,
        "watched_penalty": 0.0,
        "final_score": 0.52,
        "preference": "none",
        "watched": false,
        "saved": false
      }
    }
  ],
  "latency_ms": 130.2
}
```

## Save Feedback

```http
POST /feedback
```

Allowed actions:

```text
like
dislike
watched
save
```

Example request:

```json
{
  "user_id": "demo_user",
  "movie_id": "152601",
  "title": "Her",
  "action": "like",
  "query": "lonely futuristic romance like Her",
  "genres": "Romance, Science Fiction, Drama",
  "score": 0.82
}
```

Example response:

```json
{
  "id": 1,
  "user_id": "demo_user",
  "movie_id": "152601",
  "title": "Her",
  "query": "lonely futuristic romance like Her",
  "genres": "Romance, Science Fiction, Drama",
  "score": 0.82,
  "preference": "like",
  "watched": false,
  "saved": false,
  "created_at": "2026-06-03T00:00:00",
  "updated_at": "2026-06-03T00:00:00"
}
```

## Get User Preferences

```http
GET /feedback/{user_id}
```

Example response:

```json
[
  {
    "id": 1,
    "user_id": "demo_user",
    "movie_id": "152601",
    "title": "Her",
    "query": "lonely futuristic romance like Her",
    "genres": "Romance, Science Fiction, Drama",
    "score": 0.82,
    "preference": "like",
    "watched": true,
    "saved": true,
    "created_at": "2026-06-03T00:00:00",
    "updated_at": "2026-06-03T00:00:00"
  }
]
```

## Get Memory Summary

```http
GET /feedback/{user_id}/summary
```

Example response:

```json
{
  "user_id": "demo_user",
  "total_preferences": 1,
  "liked_movies": ["Her"],
  "disliked_movies": [],
  "watched_movies": ["Her"],
  "saved_movies": ["Her"],
  "liked_genres": {
    "Romance": 1,
    "Science Fiction": 1,
    "Drama": 1
  },
  "disliked_genres": {}
}
```

## Memory Design

The backend stores one current preference state per user/movie pair.

Like and Dislike are mutually exclusive through a single `preference` field.

Watched and Saved are independent boolean flags.

Repeated clicks update the existing row instead of creating duplicate rows.