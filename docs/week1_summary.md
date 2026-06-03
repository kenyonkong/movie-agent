# Week 1 Summary

## Goal

Build the first full-stack MVP of Movie Agent.

## Completed

### Day 1: Full-Stack Skeleton

- Initialized project structure
- Built FastAPI backend skeleton
- Built Next.js frontend skeleton
- Added health check endpoint
- Connected frontend to backend

### Day 2: Data Processing

- Added movie metadata ingestion pipeline
- Cleaned movie records
- Merged credits data
- Extracted genres, keywords, cast, and director
- Built embedding-ready movie documents
- Added validation script

### Day 3: Semantic Search

- Added embedding service abstraction
- Added local sentence-transformers embedding support
- Added optional OpenAI embedding support
- Built Chroma vector database
- Added command-line semantic search
- Added retrieval smoke test
- Added latency benchmark

### Day 4: Recommendation API

- Added typed recommendation request/response schemas
- Added recommender service
- Added `POST /recommend`
- Returned ranked movie candidates
- Added latency to API response

### Day 5: Frontend UI

- Added search UI
- Added movie result cards
- Added loading and error states
- Connected frontend to backend recommendation API
- Displayed score, reason, and document preview

### Day 6: Feedback and Memory

- Added SQLite database
- Added SQLAlchemy preference model
- Added one current preference state per user/movie pair
- Added unique constraint on `(user_id, movie_id)`
- Added Like / Dislike / Watched / Save feedback
- Made Like and Dislike mutually exclusive
- Made Watched and Save independent flags
- Added user memory summary

### Day 7: Documentation and Packaging

- Added README update
- Added system design documentation
- Added API contract
- Added demo plan
- Added resume bullet drafts
- Added Week 1 summary

## Current MVP

The current app supports:

```text
Natural-language query
   ↓
Embedding-based semantic search
   ↓
Movie recommendation cards
   ↓
Explicit feedback
   ↓
Current user preference memory
```

## Known Limitations

- User memory is stored but not yet used for reranking.
- Explanations are template-based.
- Evaluation is still basic.
- No authentication.
- No deployment yet.
- SQLite is used for local development.

## Next Week Goals

- Add memory-based reranking
- Penalize watched movies
- Boost liked genres
- Penalize disliked genres
- Add diversity and novelty scoring
- Improve explanations
- Add evaluation metrics