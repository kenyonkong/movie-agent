# Movie Agent: Agentic Movie Recommendation System

Movie Agent is a full-stack AI movie recommendation system. Users describe what they want to watch in natural language, and the system recommends movies using metadata processing, semantic search, vector retrieval, feedback memory, and personalized ranking foundations.

The project starts as a semantic movie recommender and is designed to evolve into an agentic recommendation system with tool-based retrieval, user preference memory, reranking, and grounded explanations.

## Why This Is Not Just a Chatbot

A basic chatbot may directly generate movie titles from an LLM. This project instead grounds recommendations in a movie database.

Current workflow:

```text
User natural-language query
   ↓
FastAPI recommendation endpoint
   ↓
Embedding model
   ↓
Chroma vector database
   ↓
Top-k movie candidates
   ↓
Structured recommendation response
   ↓
Next.js frontend
   ↓
User feedback
   ↓
SQLite preference memory
```

The LLM layer will later be used for grounded explanations and intent parsing, not for hallucinating movie recommendations.

## Current Week 1 MVP

Implemented:

- Movie metadata ingestion pipeline
- Embedding-ready movie document generation
- Local embedding model support
- Chroma vector database
- Natural-language semantic movie search
- FastAPI recommendation API
- Next.js frontend search UI
- SQLite user preference memory
- Like / Dislike / Watched / Save feedback
- One current preference state per user/movie pair
- Memory summary over liked/disliked genres and watched/saved movies

## Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- ChromaDB
- sentence-transformers
- Optional OpenAI embedding support

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Data / AI

- TMDB movie metadata
- Metadata cleaning pipeline
- Embedding-ready semantic movie documents
- Dense vector search
- User feedback memory

## Architecture

```text
                 ┌────────────────────┐
                 │   Next.js Frontend  │
                 │  Search + Feedback  │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │   FastAPI Backend   │
                 │ /recommend /feedback│
                 └─────────┬──────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
   ┌────────────────────┐    ┌────────────────────┐
   │  Chroma Vector DB  │    │   SQLite Database   │
   │  Movie Embeddings  │    │ User Preferences    │
   └────────────────────┘    └────────────────────┘
              ▲
              │
   ┌────────────────────┐
   │ Movie Data Pipeline │
   │ TMDB → Documents    │
   └────────────────────┘
```

## Memory Design

The app stores one current preference state per user/movie pair.

Table:

```text
user_movie_preferences
```

Uniqueness rule:

```text
(user_id, movie_id) must be unique
```

State fields:

```text
preference: "like" | "dislike" | null
watched: boolean
saved: boolean
```

Behavior:

- Clicking Like sets `preference = "like"`.
- Clicking Dislike sets `preference = "dislike"`.
- Like and Dislike are mutually exclusive.
- Clicking Watched sets `watched = true`.
- Clicking Save sets `saved = true`.
- Watched and Save are independent of Like/Dislike.
- Repeated clicks update the existing row instead of creating duplicate rows.

This prevents repeated clicks on the same movie from inflating genre preference counts.

## Project Structure

```text
movie-agent/
  backend/
    app/
      api/
        routes/
          health.py
          recommend.py
          feedback.py
      core/
        config.py
      db/
        database.py
        models.py
        schemas.py
      services/
        embedding_service.py
        vector_store.py
        recommender.py
        memory_service.py
      scripts/
        ingest_movies.py
        validate_movies.py
        build_embeddings.py
        search_movies.py
        evaluate_retrieval_smoke.py
        benchmark_search.py
        init_db.py
        inspect_feedback.py
  frontend/
    app/
      page.tsx
    components/
      SearchBar.tsx
      MovieCard.tsx
      RecommendationList.tsx
      FeedbackButtons.tsx
    lib/
      api.ts
    types/
      movie.ts
  docs/
    system_design.md
    demo_plan.md
    resume_bullets.md
    week1_summary.md
    api_contract.md
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Dataset

Place the TMDB files here:

```text
backend/data/raw/movies_metadata.csv
backend/data/raw/credits.csv
```

If using the Kaggle TMDB 5000 dataset, rename:

```text
tmdb_5000_movies.csv  -> movies_metadata.csv
tmdb_5000_credits.csv -> credits.csv
```

Run ingestion:

```bash
cd backend
python -m app.scripts.ingest_movies
python -m app.scripts.validate_movies
```

### 3. Build Vector Database

```bash
python -m app.scripts.build_embeddings
```

Test semantic search:

```bash
python -m app.scripts.search_movies "I want something like Her, lonely and futuristic, but not too slow"
```

### 4. Initialize SQLite Database

```bash
python -m app.scripts.init_db
```

### 5. Run Backend

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

### 6. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## API Overview

### Recommendation

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

### Feedback

```http
POST /feedback
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

### Memory Summary

```http
GET /feedback/{user_id}/summary
```

## Example Queries

```text
I want something like Her, lonely and futuristic, but not too slow
A dark psychological thriller with obsession and mystery
A funny comfort movie about friendship and family
An epic fantasy adventure with battles and magical worlds
A quiet emotional sci-fi movie about memory and identity
```

## Screenshots

Screenshots will be added after the Week 1 UI checkpoint.

Planned screenshots:

- Search page
- Recommendation results
- Feedback buttons
- User memory summary
- FastAPI docs

## Current Limitations

- Recommendations currently use semantic similarity only.
- User memory is stored but not yet used for reranking.
- Explanations are currently simple template-based explanations.
- No authentication or multi-user login yet.
- Local SQLite is used for MVP development.
- Evaluation metrics are currently smoke tests and latency benchmarks.

## Roadmap

Next steps:

- Memory-based reranking
- Watched movie filtering or penalty
- Genre preference boosts and penalties
- Diversity and novelty scoring
- LLM-grounded explanations
- Evaluation dashboard
- Demo video and screenshots
- Optional deployment
- PostgreSQL or pgvector migration

## Resume Summary

Built a full-stack AI movie recommendation system using FastAPI, Next.js, Chroma, SQLAlchemy, and dense embeddings. The system processes movie metadata into embedding-ready documents, retrieves movies from natural-language queries, and stores one current user preference state per user/movie pair for future personalized reranking.


## MovieAgent Orchestration

The MovieAgent is a controlled workflow orchestrator rather than an
unrestricted autonomous LLM agent.

Its responsibilities are:

1. Interpret the request through the intent parser.
2. Load the user's recommendation memory.
3. Retrieve candidates from the configured vector index.
4. Apply watched filtering and fallback rules.
5. Produce a heuristic shortlist.
6. Optionally pass that shortlist to a bounded LLM reranker.
7. Generate grounded explanations.
8. Return a validated response and sanitized trace.

The MovieAgent does not own the implementation details of retrieval,
memory, ranking, or explanation. Those remain separate injectable tools.

This separation improves testability and allows individual tools to be
upgraded without rewriting the orchestration layer.