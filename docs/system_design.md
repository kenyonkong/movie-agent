# System Design

## Overview

Movie Agent is a full-stack AI movie recommendation system for natural-language movie discovery.

Instead of asking an LLM to invent movie titles directly, the system grounds recommendations in a real movie metadata dataset. The current Week 1 MVP supports semantic retrieval, a FastAPI recommendation API, a Next.js frontend, and persistent user preference memory.

## Architecture

```text
User
  ↓
Next.js Frontend
  ↓
FastAPI Backend
  ↓
Recommendation Service
  ↓
Embedding Service
  ↓
Chroma Vector Store
  ↓
Movie Candidates
  ↓
Recommendation Response
  ↓
User Feedback
  ↓
SQLite Preference Memory
```

## Main Components

### 1. Data Processing Pipeline

Raw TMDB movie data is cleaned and transformed into structured movie records.

Inputs:

```text
backend/data/raw/movies_metadata.csv
backend/data/raw/credits.csv
```

Outputs:

```text
backend/data/processed/movies_clean.csv
backend/data/processed/movie_documents.jsonl
```

Each movie is converted into an embedding-ready document containing title, release year, genres, overview, tagline, keywords, main cast, director, runtime, average rating, and popularity.

This gives the embedding model richer semantic context than just the movie title.

### 2. Embedding Service

The embedding layer converts movie documents and user queries into dense vectors.

The code supports:

- Local sentence-transformers embeddings
- Optional OpenAI embeddings

This abstraction allows the project to switch embedding providers without changing the recommender logic.

### 3. Vector Store

Chroma stores movie document embeddings.

Each stored item contains:

```text
id
document
metadata
embedding
```

At query time, the backend embeds the user's natural-language query and retrieves the nearest movie document vectors.

### 4. Recommendation API

The FastAPI backend exposes:

```http
POST /recommend
```

The endpoint accepts:

```text
user_id
query
top_k
```

It returns ranked movie recommendations with metadata, retrieval score, vector distance, document preview, explanation, and latency.

### 5. Feedback and Memory

The app stores one current preference state per user/movie pair.

Table:

```text
user_movie_preferences
```

Unique constraint:

```text
(user_id, movie_id)
```

State fields:

```text
preference: "like" | "dislike" | null
watched: boolean
saved: boolean
```

This avoids duplicate feedback rows and prevents repeated clicks from inflating genre counts.

## Why Current Preference State Instead of Event Log?

An event-log design would store every click:

```text
Like Her
Like Her
Like Her
```

That is useful for analytics, but it caused a problem for this MVP: repeated clicks on the same movie inflated genre counts.

The fixed design stores one current state:

```text
Her -> preference = like, watched = false, saved = false
```

Repeated clicks update the same row instead of creating duplicates.

## Tradeoffs

### SQLite vs PostgreSQL

SQLite was chosen for local development because it is simple and requires no separate database server.

PostgreSQL would be better for production deployment, concurrent writes, and scalability.

### Chroma vs FAISS vs pgvector

Chroma was chosen for fast local development and persistent vector search.

FAISS would provide more low-level vector index control.

pgvector would be useful if the project later moves to PostgreSQL and needs relational data and vector search in one database.

### Template Explanations vs LLM Explanations

Current explanations are simple and metadata-grounded.

LLM explanations will be added later after retrieval and reranking are stable. This avoids turning the project into an ungrounded chatbot.

## Future Design

The next major feature is memory-based reranking.

A future scoring function may look like:

```text
final_score =
  semantic_score
  + liked_genre_boost
  - disliked_genre_penalty
  - watched_penalty
  + novelty_score
  + diversity_score
```

This will turn the current semantic search system into a personalized recommendation system.