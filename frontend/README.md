# Movie Agent frontend

The frontend is a Next.js 16 and React 19 client for the FastAPI Movie Agent.
It provides natural-language search, pipeline controls, recommendation cards,
feedback actions, constraint diagnostics, execution traces, and title-only
catalog browsing.

The app has three routes:

- `/` — semantic recommendations
- `/movies` — movie title search
- `/reviews` — review-workspace placeholder

Review buttons are intentionally disabled until the review API and persistence
workflow are implemented.

## Setup

```powershell
npm install
npm run dev
```

The API defaults to `http://localhost:8000`. Override it in `.env.local` with:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Checks

```powershell
npm run typecheck
npm run lint
npm run build
```

Run all three with `npm run check`.
