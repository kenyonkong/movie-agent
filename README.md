# Movie Agent

Movie Agent is a full-stack AI movie recommendation system. Users can describe what they want to watch in natural language, and the system recommends movies using semantic search, personalized reranking, user feedback memory, and LLM-generated explanations.

## Project Goal

The goal is to build a resume-ready AI/SDE project that is more than a chatbot. The system will use a tool-based recommendation workflow:

1. Parse user intent
2. Retrieve movie candidates
3. Load user preference memory
4. Rerank candidates
5. Generate grounded explanations
6. Update memory from user feedback

## Tech Stack

- Backend: FastAPI, Python
- Frontend: Next.js, React, TypeScript
- Database: SQLite first, PostgreSQL later
- Vector Search: Chroma first, FAISS or pgvector later
- Embeddings: OpenAI or local embedding model
- LLM: Used for explanation, not for ungrounded movie generation

## Dataset Setup

This project currently uses the TMDB 5000 Movie Dataset.

Raw files:

```text
backend/data/raw/movies_metadata.csv
backend/data/raw/credits.csv
```

## Current Status

Day 1:
- [x] Backend FastAPI skeleton
- [x] Health check API
- [x] Frontend Next.js skeleton
- [x] Frontend-to-backend connection

Day 2:
- [x] Raw TMDB files are placed in backend/data/raw/
- [x] python -m app.scripts.ingest_movies runs successfully
- [x] movies_clean.csv is generated
- [x] movie_documents.jsonl is generated
- [x] python -m app.scripts.validate_movies runs successfully

Day 3:
- [x] Embedding service abstraction
- [x] Local embedding support
- [x] Optional OpenAI embedding support
- [x] Chroma vector store
- [x] Vector database build script
- [x] Command-line semantic search
- [x] Retrieval smoke test
- [x] Search latency benchmark

Day 4:
- [x] Recommendation request/response schemas
- [x] Recommender service layer
- [x] POST /recommend API
- [x] Recommendation debug endpoint
- [x] API latency measurement
- [x] Manual tests through FastAPI docs
## Planned Features

- Movie metadata processing
- Embedding-based semantic search
- Top-k movie recommendation
- Personalized reranking
- Like / dislike / watched / save feedback
- User preference memory
- Evaluation metrics: relevance, diversity, novelty, latency
- Demo video and screenshots