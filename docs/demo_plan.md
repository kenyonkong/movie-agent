# Demo Plan

## Goal

Show that Movie Agent is a full-stack AI recommendation system, not a basic chatbot.

The demo should show:

1. Natural-language movie search
2. Semantic recommendations
3. Recommendation metadata
4. Feedback buttons
5. Fixed user memory design
6. Memory summary update

## Demo Setup

Start backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Start frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

## Demo Flow

### Step 1: Run a Natural-Language Query

Use:

```text
I want something like Her, lonely and futuristic, but not too slow
```

Expected result:

- Movie cards appear.
- Each card shows title, year, genres, score, explanation, and document preview.
- Backend latency is displayed.

### Step 2: Explain Retrieval

Say:

```text
The frontend sends the query to a FastAPI backend. The backend embeds the query and searches a Chroma vector database built from movie metadata documents.
```

### Step 3: Show Feedback

Click Like on one movie.

Expected result:

- The Like button becomes active.
- The memory summary updates.
- Liked genres appear.

### Step 4: Show Duplicate-Click Fix

Click Like on the same movie multiple times.

Expected result:

- The same database row is updated.
- No duplicate rows are created.
- Genre counts do not keep increasing.

### Step 5: Show Mutually Exclusive Like/Dislike

Click Dislike on the same movie.

Expected result:

- `preference` changes from `"like"` to `"dislike"`.
- Like and Dislike are not counted simultaneously.

### Step 6: Show Independent Watched/Saved Flags

Click Watched and Save.

Expected result:

- `watched = true`
- `saved = true`
- These flags do not erase Like/Dislike preference.

### Step 7: Inspect Backend State

Run:

```bash
cd backend
python -m app.scripts.inspect_feedback
```

Expected result:

```text
one row per user/movie pair
preference=dislike
watched=True
saved=True
```

## Demo Talking Points

- Recommendations are grounded in a real movie dataset.
- Semantic search handles natural-language movie intent.
- Feedback is stored as current preference state, not raw click events.
- Like/dislike are mutually exclusive.
- Watched/saved are independent.
- The next stage will use memory for personalized reranking.