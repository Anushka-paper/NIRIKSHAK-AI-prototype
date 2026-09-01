# NIRIKSHAK AI Deployment

## Fastest demo deployment

Deploy the backend on Render and the frontend on Vercel.

### Backend: Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Render will read `render.yaml` and create `nirikshak-ai-api`.
4. After the service is live, copy its URL, for example:
   `https://nirikshak-ai-api.onrender.com`

The backend seeds a demo SQLite database from `data/synthetic/raw_csvs` on startup.

The demo Render config starts with `CORS_ORIGINS=*` so Vercel can connect immediately. After deploying the frontend, tighten the backend `CORS_ORIGINS` environment variable in Render to your Vercel URL, for example:

```text
https://your-vercel-app.vercel.app
```

For multiple origins, use comma-separated values.

### Frontend: Vercel

1. Import the same GitHub repository in Vercel.
2. Set the project root directory to `frontend`.
3. Add this environment variable:

```text
NEXT_PUBLIC_API_URL=https://your-render-api-url.onrender.com
```

4. Deploy.

### Local checks

From `frontend`:

```bash
npm run build
```

From `backend/app` after installing dependencies:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/health
```

## Production database

For a more durable deployment, replace the Render `DATABASE_URL` with a hosted PostgreSQL URL from Supabase, Neon, or Render Postgres. Keep `AUTO_SEED_SQLITE=false` when using Postgres.
