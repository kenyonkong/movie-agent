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
  "top_k": 5
}
```

Example response:

```json
{
  "user_id": "demo_user",
  "query": "I want something like Her, lonely and futuristic, but not too slow",
  "top_k": 5,
  "results": [
    {
      "movie_id": "152601",
      "title": "Her",
      "release_year": 2013,
      "genres": "Romance, Science Fiction, Drama",
      "score": 0.48,
      "distance": 1.08,
      "reason": "Recommended because Her is semantically close to your query and belongs to genres such as Romance, Science Fiction, Drama.",
      "document_preview": "Title: Her (2013)..."
    }
  ],
  "latency_ms": 120.5
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