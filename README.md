# Movie Agent

Movie Agent is a full-stack, agentic movie recommendation system built with Next.js, FastAPI, ChromaDB, SQLite, and optional OpenAI reasoning. Users describe what they want to watch in natural language, and the system retrieves real catalog movies, applies explicit constraints, personalizes the ranking from feedback memory, and explains the final results.

The key design principle is that the LLM is never an unrestricted source of movie recommendations. Retrieval, catalog metadata, deterministic validation, and fallback logic remain authoritative.

## Current Status

Implemented:

- TMDB metadata ingestion and cleaning
- Embedding-ready movie document generation
- Local or OpenAI embeddings
- Persistent Chroma vector search
- Template or OpenAI structured intent parsing
- Hard-constraint planning and enforcement
- SQLite feedback and preference memory
- Watched-movie filtering with controlled fallback
- Transparent heuristic reranking
- Optional bounded LLM reranking over an allowlisted shortlist
- Template or OpenAI grounded explanations
- Sanitized per-request agent traces
- Next.js recommendation and feedback interface
- End-to-end evaluation across retrieval and agent configurations

Review functionality is not currently part of the active API or frontend. It is described as future work below.

## Why This Is More Than a Chatbot

A general chatbot can generate plausible movie titles from model memory. Movie Agent instead grounds every result in the indexed catalog:

```text
Natural-language request
        |
        v
Structured intent + hard constraints
        |
        v
Chroma semantic retrieval
        |
        v
Deterministic constraint validation
        |
        v
SQLite preference memory
        |
        v
Heuristic shortlist
        |
        +---- optional bounded LLM reranking
        |
        v
Grounded explanations + typed API response
```

The LLM may parse intent, reorder a finite shortlist, or explain already selected movies. It cannot introduce arbitrary movies into the response.

## Recommendation Pipeline

`MovieAgent` executes one explicit workflow per request:

1. Validate that the configured vector collection is available.
2. Parse the query into structured intent.
3. Convert explicit requirements into a hard-constraint plan.
4. Load the user's feedback memory from SQLite.
5. Retrieve a broad semantic candidate pool from Chroma.
6. Revalidate all active constraints in Python.
7. Remove watched movies when possible.
8. Score and diversify a heuristic shortlist.
9. Optionally ask an LLM to reorder only allowlisted shortlist IDs.
10. Generate grounded explanations for the selected results.
11. Return a Pydantic-validated response and optional execution trace.

This fixed orchestration makes tool order, latency, failures, and fallbacks observable and testable.

### Hard Constraints

Explicit requirements can include:

- Director or cast
- Required or excluded genres
- Original language
- Minimum or maximum runtime
- Release-year range
- Minimum vote average or vote count

Constraints are pushed into Chroma metadata filtering for efficiency and then checked again in Python for correctness. When too few valid results exist, the system returns a shortfall instead of filling the response with invalid movies.

### Heuristic Ranking

The current deterministic score is:

```text
base_score =
    0.90 * semantic_score
  + 0.03 * preference_score
  + 0.01 * novelty_score
  + saved_boost
  - watched_penalty

final_score = base_score - diversity_penalty
```

The semantic score dominates. Feedback, novelty, watched status, saved status, and genre diversity make smaller, explainable adjustments. Diversity uses greedy selection with genre Jaccard overlap.

### Bounded LLM Reranking

When enabled, the LLM receives a compact heuristic shortlist, an allowlist of movie IDs, parsed intent, selected metadata, and a sanitized preference summary. Structured Outputs require a list of existing IDs and concise reasons.

The backend rejects:

- IDs outside the shortlist
- Duplicate IDs
- The wrong number of selections
- Empty selection reasons
- Malformed or missing structured output

Any failure falls back to the deterministic heuristic order.

### Feedback Memory

SQLite stores one current preference state per `(user_id, movie_id)` pair:

```text
preference: "like" | "dislike" | null
watched: boolean
saved: boolean
```

Like and dislike are mutually exclusive. Watched and saved are independent. Repeated actions update the existing row instead of creating duplicate events, preventing repeated clicks from inflating genre counts.

## Tech Stack

### Backend

- Python 3
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- ChromaDB
- sentence-transformers
- OpenAI Python SDK
- pytest

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- ESLint

### Data and Evaluation

- TMDB movie metadata
- JSONL semantic documents
- Dense-vector retrieval
- Manually curated relevance labels and graded judgments
- Hit@K, precision, recall, MRR, nDCG, constraint accuracy, diversity, novelty, latency, fallback, and token metrics

## Project Structure

```text
movie agent/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                  Main recommendation page
│   │   ├── layout.tsx                Root layout
│   │   └── globals.css               Global styling
│   ├── components/
│   │   ├── SearchBar.tsx             Query and pipeline controls
│   │   ├── RecommendationList.tsx    Results and diagnostics
│   │   ├── MovieCard.tsx             Movie presentation
│   │   ├── FeedbackButtons.tsx       Like/dislike/watched/save controls
│   │   └── AgentTracePanel.tsx       Sanitized workflow trace
│   ├── lib/api.ts                    FastAPI client
│   └── types/movie.ts                TypeScript API contracts
│
├── backend/
│   ├── app/
│   │   ├── main.py                   FastAPI application entry point
│   │   ├── api/routes/
│   │   │   ├── health.py             Health endpoint
│   │   │   ├── recommend.py          Recommendation endpoint
│   │   │   └── feedback.py           Feedback and memory endpoints
│   │   ├── agents/
│   │   │   ├── movie_agent.py        Controlled workflow orchestrator
│   │   │   ├── state.py              Per-request pipeline state
│   │   │   └── tracing.py            Sanitized execution trace
│   │   ├── services/
│   │   │   ├── intent_parser.py      Template/OpenAI intent parsing
│   │   │   ├── constraint_service.py Chroma pushdown + Python validation
│   │   │   ├── embedding_service.py  Local/OpenAI embeddings
│   │   │   ├── vector_store.py       Persistent Chroma retrieval
│   │   │   ├── memory_service.py     Preference persistence and summaries
│   │   │   ├── reranker.py           Heuristic scoring and diversity
│   │   │   ├── bounded_llm_reranker.py
│   │   │   ├── explanation_service.py
│   │   │   └── recommendation_formatter.py
│   │   ├── db/                       SQLAlchemy models and Pydantic schemas
│   │   ├── evaluation/               Evaluation runner and metrics
│   │   └── scripts/                  Ingestion, indexing, search, and eval
│   ├── data/                         Raw and processed movie data
│   ├── chroma_db/                    Persistent vector collections
│   ├── eval/end_to_end/              Queries, judgments, configs, reports
│   ├── tests/                         pytest tests
│   ├── movie_agent.db                Local SQLite database
│   ├── requirements.txt
│   └── .env.example
│
├── docs/                              Design notes and project history
└── README.md
```

## Local Setup

### 1. Backend environment

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

The default configuration uses local embeddings, template intent parsing, template explanations, and disables LLM reranking. An OpenAI API key is only required when an OpenAI-backed feature is enabled.

### 2. Prepare the catalog

For CSV ingestion, place the source files at:

```text
backend/data/raw/movies_metadata.csv
backend/data/raw/credits.csv
```

Then run:

```powershell
python -m app.scripts.ingest_movies
python -m app.scripts.build_embeddings
```

The repository also contains `ingest_tmdb_api.py` for building the catalog from the TMDB API. Set `TMDB_API_READ_ACCESS_TOKEN` before using that path.

Test the active vector collection:

```powershell
python -m app.scripts.search_movies "a quiet emotional science-fiction movie"
```

### 3. Initialize SQLite

```powershell
python -m app.scripts.init_db
```

### 4. Run FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Debug configuration: `http://localhost:8000/recommend/debug`

### 5. Run Next.js

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Configuration

Important backend environment variables are documented in `backend/.env.example`:

| Variable | Typical values | Purpose |
|---|---|---|
| `EMBEDDING_PROVIDER` | `local`, `openai` | Catalog/query embedding provider |
| `LOCAL_EMBEDDING_MODEL` | sentence-transformers model | Local embedding model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `INTENT_PARSER_PROVIDER` | `template`, `openai` | Query interpretation provider |
| `EXPLANATION_PROVIDER` | `template`, `openai` | Explanation provider |
| `LLM_RERANKER_PROVIDER` | `disabled`, `openai` | Optional bounded reranker |
| `LLM_RERANKER_SHORTLIST_SIZE` | `15` | Maximum heuristic shortlist exposed to the LLM |
| `CHROMA_COLLECTION_NAME` | optional override | Explicit vector collection |
| `DATABASE_URL` | SQLAlchemy URL | Preference database connection |

Changing the embedding model requires a compatible Chroma collection built with that model.

## API Overview

### Health

```http
GET /health
```

### Recommend movies

```http
POST /recommend
```

```json
{
  "user_id": "demo_user",
  "query": "A thoughtful science-fiction romance like Her, but under two hours",
  "top_k": 5,
  "include_watched": false,
  "use_llm_intent": true,
  "enforce_hard_constraints": true,
  "use_llm_reranker": false,
  "use_llm_explanations": false,
  "include_agent_trace": true
}
```

The response includes parsed intent, the retrieval query, a constraint report, ranking signals, provider/fallback information, recommendations, latency, and an optional trace.

### Save feedback

```http
POST /feedback/
```

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

Supported actions are like, dislike, watched, and save.

### Read feedback memory

```http
GET /feedback/{user_id}
GET /feedback/{user_id}/summary
```

## Evaluation

The end-to-end harness compares raw retrieval, intent-enhanced retrieval, heuristic agent ranking, and bounded LLM ranking over the same query set and catalog.

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.run_evaluation
```

Run one configuration:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.run_evaluation `
  --config openai_agent_llm
```

Recorded Day 17 results:

| Configuration | Hit@5 | nDCG@5 | Constraint accuracy | P50 latency |
|---|---:|---:|---:|---:|
| Local raw retrieval | 0.500 | 0.3528 | 0.4778 | 12.70 ms |
| OpenAI raw retrieval | 0.625 | 0.5827 | 0.8500 | 222.53 ms |
| OpenAI intent retrieval | 0.625 | 0.5247 | 0.8055 | 1642.01 ms |
| Agent heuristic | 0.500 | 0.5309 | 0.8055 | 1539.34 ms |
| Agent bounded LLM | **0.750** | **0.7653** | **0.9556** | 4280.91 ms |

These results come from an eight-query development benchmark with curated labels. They demonstrate the evaluation pipeline and quality/latency tradeoff; they are not production-scale statistical claims.

## Development Checks

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

Frontend checks:

```powershell
cd frontend
npx tsc --noEmit
npm run lint
npm run build
```

Known development cleanup:

- The MovieAgent unit-test fake needs to accept the vector store's newer `where` argument.
- `FeedbackButtons.tsx` currently triggers the React `set-state-in-effect` lint rule.
- The OpenAI explanation prompt contains an older scoring-weight description and should be synchronized with the current heuristic formula.
- The conservative template intent parser's language-pattern matching should use regex search rather than literal substring matching.

## Current Limitations

- No authentication or account management; `demo_user` is the default identity.
- SQLite is appropriate for the local MVP but not the intended multi-instance production database.
- Heuristic weights are manually tuned rather than learned from interaction data.
- OpenAI intent parsing, reranking, and explanations add latency and usage cost.
- Template intent parsing intentionally recognizes only a limited set of explicit phrases.
- Evaluation uses a small, manually curated development set.
- Review creation, editing, publishing, and display are not active features.

## Future Direction: Movie Reviews

Review functionality should be introduced as a separate, user-authored content workflow rather than mixed directly into feedback buttons. Like, dislike, watched, and saved are lightweight ranking signals; a review is richer content with its own lifecycle, validation, and privacy concerns.

### Proposed data model

Create a `movie_reviews` table with one review per user/movie pair for the first version:

```text
id
user_id
movie_id
movie_title_snapshot
rating                 optional numeric rating
headline               optional short title
body                    review text
contains_spoilers       boolean
status                  draft | published
created_at
updated_at

UNIQUE(user_id, movie_id)
```

The catalog remains authoritative for movie metadata. Only a title snapshot should be stored with the review for display/history resilience.

### Proposed backend design

Add review schemas, a `ReviewService`, and an independently registered router:

```http
POST   /reviews
GET    /reviews/{review_id}
GET    /reviews/user/{user_id}
GET    /reviews/movie/{movie_id}
PATCH  /reviews/{review_id}
DELETE /reviews/{review_id}
```

The service should:

- Validate the movie ID against the local catalog.
- Enforce rating and text-length limits with Pydantic.
- Keep draft and published states explicit.
- Confirm review ownership before update or deletion once authentication exists.
- Use database migrations rather than relying only on startup table creation.
- Return typed response schemas without leaking internal database objects.

### Proposed frontend design

Add a review editor reachable from a movie card or movie detail view:

- Rating input, headline, body, and spoiler flag
- Save draft, publish, edit, and delete actions
- User review history
- Movie-level review list with spoiler text hidden by default
- Clear separation between private preference actions and published review content

### Recommendation integration

The first review release should not place raw review text directly into recommendation prompts. A safer progression is:

1. Ship review CRUD independently of ranking.
2. Derive explicit rating/sentiment signals only from the user's own published reviews.
3. Add those signals to the existing memory summary with transparent weights.
4. Evaluate relevance and personalization changes before enabling them by default.
5. If semantic review search is later needed, index reviews in a separate Chroma collection so catalog retrieval and user-generated content remain isolated.

This preserves the existing guarantee that every recommended movie comes from the catalog and prevents untrusted review text from acting as instructions to an LLM.

### Quality and safety work

Before reviews become public or multi-user, add:

- Authentication and authorization
- Input sanitization and output escaping
- Spoiler handling
- Rate limiting
- Abuse reporting and moderation states
- Pagination and sorting
- Unit, API, permission, and frontend interaction tests
- Review-specific evaluation for usefulness, toxicity, and prompt-injection resistance

## Broader Roadmap

- Fix the current test, lint, parser, and explanation-prompt inconsistencies
- Add automated API integration tests
- Add authentication and persistent user profiles
- Build the review workflow described above
- Expand human relevance judgments and repeat LLM evaluations
- Tune heuristic weights or evaluate a learned-to-rank model
- Cache safe model outputs and reduce LLM latency
- Add screenshots and a short demo video
- Deploy the frontend, API, database, and vector store
- Evaluate PostgreSQL/pgvector for production persistence

## Resume Summary

Built a full-stack agentic movie recommendation system using Next.js, FastAPI, ChromaDB, SQLAlchemy, SQLite, dense embeddings, and optional OpenAI Structured Outputs. The system converts natural-language requests into semantic intent and deterministic constraints, retrieves catalog-grounded candidates, personalizes and diversifies results from feedback memory, safely bounds LLM reranking to allowlisted movie IDs, and evaluates relevance, constraint adherence, diversity, latency, fallbacks, and token usage.

On an eight-query development benchmark, the complete bounded-LLM configuration achieved 75% Hit@5, 0.7653 nDCG@5, and 95.56% individual constraint-check accuracy, with the expected latency and token-cost tradeoff.
