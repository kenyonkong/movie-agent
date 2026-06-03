# Resume Bullets

## Current Week 1 Version

- Built a full-stack AI movie recommendation system using FastAPI, Next.js, Chroma, SQLAlchemy, and dense embeddings, enabling natural-language movie search over metadata-derived semantic documents.

- Implemented a movie metadata ingestion pipeline that cleans TMDB records and converts plot, genre, cast, director, keyword, runtime, rating, and popularity fields into embedding-ready documents for vector retrieval.

- Developed a semantic retrieval backend using local sentence-transformer embeddings and Chroma vector search, exposing ranked movie candidates through a typed FastAPI recommendation endpoint.

- Built a persistent user preference memory layer with SQLite and SQLAlchemy, storing one current preference state per user/movie pair with mutually exclusive like/dislike and independent watched/saved flags.

- Created a Next.js and TypeScript frontend for natural-language movie discovery, displaying ranked recommendations with scores, metadata, explanations, latency, and feedback controls.

## Stronger Final Version After Reranking

- Designed and built a full-stack AI recommendation agent using FastAPI, Next.js, Chroma, SQLAlchemy, and dense embeddings to retrieve, rerank, and explain movie recommendations from natural-language user intent.

- Implemented a feedback-driven personalization layer that stores current user/movie preference states and uses liked genres, disliked genres, watched history, and saved movies as ranking signals.

- Developed a modular recommendation pipeline separating data ingestion, embedding generation, vector retrieval, user memory, reranking, explanation, and evaluation layers.

- Added evaluation metrics for recommendation relevance, diversity, novelty, and latency, enabling systematic comparison of retrieval-only and personalized reranking strategies.

## Interview Short Pitch

Movie Agent is a full-stack AI recommendation system that takes natural-language movie preferences, retrieves candidates from a vector database built from movie metadata, and stores explicit user feedback as persistent preference memory. Unlike a basic chatbot, recommendations are grounded in a real movie dataset, and the architecture separates retrieval, memory, reranking, and explanation.
EOF