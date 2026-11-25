# System Design

## Overview

Movie Agent is a full-stack, catalog-grounded recommendation system. It
combines semantic retrieval, deterministic constraints, explicit preference
memory, transparent ranking, optional bounded LLM reasoning, and evaluation.

The catalog and deterministic validators remain authoritative. LLMs may parse
intent, reorder an allowlisted shortlist, or explain selected movies; they may
not introduce arbitrary recommendations.

## Request flow

```text
Next.js UI
  -> Recommendations route
     -> FastAPI recommendation endpoint
     -> structured intent and hard-constraint plan
     -> Chroma semantic retrieval with metadata pushdown
     -> deterministic Python constraint validation
     -> SQLite preference-memory lookup
     -> watched filtering and heuristic reranking
     -> optional bounded LLM reranking
     -> grounded explanations and typed response
  -> Browse Movies route
     -> FastAPI title-search endpoint
     -> local processed CSV catalog
     -> compact typed movie metadata response
  -> My Reviews route
     -> placeholder only; no persistence yet
```

`MovieAgent` owns this fixed orchestration order. A per-request state object
holds intermediate values, while the tracer records sanitized step status,
duration, counts, providers, and fallback information.

## Catalog and retrieval

The TMDB ingestion pipeline downloads candidate IDs, retrieves movie details,
credits, and keywords, removes invalid or low-quality records, deduplicates the
catalog, and writes CSV plus JSONL semantic documents.

The browse workflow reads compact fields from the processed CSV on first use
and caches them in the API process. It performs case-insensitive substring
matching against normalized titles only; director, cast, and other metadata are
returned for display but are not searchable. Matching movies are ordered by
descending TMDB popularity before pagination is applied.

The embedding layer supports local SentenceTransformers and OpenAI embeddings.
Each provider/model configuration receives a separate persistent Chroma
collection. Movie metadata is stored alongside vectors so eligible constraints
can be pushed into retrieval.

## Intent and exact constraints

Intent parsing supports a conservative template parser and optional OpenAI
Structured Outputs. The result separates soft preferences from enforceable
hard constraints.

Supported hard constraints include director, cast, required and excluded
genres, original language, runtime, release year, vote average, and vote count.
Chroma filtering narrows the search, but Python validation is the final
authority. The response reports rejected candidates and returns a short list
rather than filling it with invalid movies.

## Preference memory and ranking

SQLite stores one current state per `(user_id, movie_id)` pair:

```text
preference: like | dislike | null
watched: boolean
saved: boolean
```

The design is intentionally state-based rather than an append-only click log,
so repeated actions do not inflate preference counts.

The heuristic score is dominated by semantic relevance, with smaller genre
preference and novelty signals, a saved boost, a watched penalty, and greedy
genre-diversity selection. Every returned recommendation exposes its ranking
signals.

## Optional LLM stages

OpenAI-backed intent parsing, reranking, and explanations are independently
configurable. The bounded reranker receives only a heuristic shortlist and must
return existing movie IDs. Invalid IDs, duplicates, wrong selection counts,
empty reasons, missing output, or provider failures trigger deterministic
fallback.

Explanations are generated only after selection. Both template and OpenAI
explanations use retrieved metadata and ranking signals rather than model
memory.

## Evaluation

The evaluation harness compares raw retrieval, intent-enhanced retrieval,
heuristic agent ranking, and bounded LLM ranking over common query and judgment
sets. It records relevance, ranking, constraint accuracy, diversity, novelty,
latency, token use, and fallback metrics.

## Current deployment boundaries

- `demo_user` is a development identity; authentication is not implemented.
- SQLite and local Chroma are suitable for the local application, not a
  multi-instance production deployment.
- Database tables are created at startup; schema migrations are future work.
- OpenAI stages add latency and usage cost and remain optional.
- The evaluation set is a small development benchmark.

## Movie reviews

SQLite stores one review per user and movie. The API accepts review text and
an integer rating from 1 to 10, displayed on the frontend in half-star steps.
My Reviews lists entries by descending update time. The frontend uses the
existing demo identity while authentication is pending.
