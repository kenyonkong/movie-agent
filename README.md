# Movie Agent

A personal movie discovery and review app built with Next.js, FastAPI, Chroma, and SQLite.

- **Recommendations (`/`)** turns a natural-language request into catalog-grounded suggestions. It applies metadata constraints, uses saved feedback and watched history, and can optionally use OpenAI for intent parsing, reranking, and explanations.
- **Browse Movies (`/movies`)** searches titles with punctuation normalization and as-you-type suggestions. Results are sorted by catalog popularity.
- **My Reviews (`/reviews`)** shows posters, whole-star ratings from 1 to 5, and review text, with 10 entries per page. Write or edit reviews from movie cards or My Reviews. Saving a review marks the movie as watched. Imported reviews use their original Douban dates and display English translations when available.

- **Taste Profile (`/taste-profile`)** shows a current paragraph from the full review history, recurring likes and dislikes, and an interactive timeline with original review evidence.

The local app uses a shared `demo_user` identity. Recommendation personalization uses feedback and watched history.

## Run locally

Python 3.12 and Node.js 22 are used in CI. From the repository root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If you already have a local catalog and matching Chroma index, reuse them. For a fresh setup, set `TMDB_API_READ_ACCESS_TOKEN` in `backend/.env`, then build both:

```powershell
python -m app.scripts.ingest_tmdb_api
python -m app.scripts.build_embeddings
```

TMDB ingestion includes the IMDb IDs and artwork used by Douban matching and movie cards. Local embeddings are the default. Use a valid `OPENAI_API_KEY` when enabling OpenAI-backed features.

Start the API from `backend/` and the frontend from `frontend/` in separate terminals:

```powershell
# backend/
python -m uvicorn app.main:app --reload

# frontend/
npm ci
npm run dev
```

Open the app at <http://localhost:3000> and the API docs at <http://localhost:8000/docs>. The API creates the SQLite tables at startup. Use `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` to override the API address.

## Import Douban reviews

Keep the CSV export, Douban-to-IMDb map, prepared JSON, and database backups local. The repository ignores `douban data/`, local datasets, and SQLite files.

From `backend/`, with the virtual environment active:

```powershell
python -m app.scripts.prepare_douban_reviews `
  --source "../douban data/douban_movie_record.csv" `
  --mapping "../douban data/douban_imdb_map.json" `
  --output "../douban data/douban_reviews_prepared.json"

python -m app.scripts.import_douban_reviews "../douban data/douban_reviews_prepared.json"
```

Preparation keeps entries with both a valid rating and a short review, matches them to the catalog by IMDb ID, and saves the original text alongside any English translation. Translation sends review text to the configured OpenAI model and resumes from the JSON checkpoint. Use `--prepare-only` to build the match file without calling OpenAI.

Back up SQLite before importing. The importer defaults to `demo_user`, skips unmatched entries and existing reviews, and preserves the original marked dates. My Reviews orders imported entries by marked date and other entries by last update, newest first.

## Build the experimental taste profile

From `backend/` with the virtual environment active and `OPENAI_API_KEY` configured, run:

```powershell
python -m app.scripts.build_taste_profile
```

Reviews are ordered by the Douban marked date or local review update time, with ties broken by review ID. The first pass extracts observations from the original text without star ratings and verifies each quotation. SQLite caches each extraction, including empty results. Existing 50-review observations are reused when upgrading the original experiment.

The second pass summarizes all observations available at 50 reviews and every 30 thereafter. The current summary also includes any unfinished period. Each sentence links to evidence from multiple films. Bubble area counts distinct supporting films, and each chart bar shows the share of reviews supporting the selected preference in that period. Stable chart labels make periods comparable. Observations outside those labels still inform the summary.

Once initialized, saving or editing a review in the app triggers a background refresh. The page reads the last complete profile and flags a pending change. Rerun the command after a bulk import or failed refresh. Unchanged extractions and completed milestones are reused. Use `--model` to override `OPENAI_EXPLANATION_MODEL`.

## Development

```powershell
# backend/
python -m pytest tests -q

# frontend/
npm run check
```

GitHub Actions runs the backend tests and the frontend type checks, lint, and production build. See [system design](docs/system_design.md) for the recommendation pipeline and [API contract](docs/api_contract.md) for endpoint details.
