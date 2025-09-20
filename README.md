# Futures Signal App (Deploy-ready)

This repo is a minimal deployable demo of a Futures Signal App using real price data via ccxt.

## What it includes
- FastAPI backend that fetches prices via ccxt and produces a simple EMA-based signal.
- Simple frontend (static HTML + JS) that calls backend API.
- Dockerfile and render.yaml to deploy to Render (free tier).

## Deploy to Render (quick)
1. Create a GitHub repo and upload this project (or fork after uploading).
2. Create account at https://dashboard.render.com
3. Click "New" -> "Blueprint" and connect your repo, Render will read `render.yaml`.
4. Set environment variables in Render if you want to override defaults (SYMBOL, EXCHANGE, API_KEY/API_SECRET optional).
5. Deploy. After build, open your service URL and the frontend will be served by the backend.

## Notes & security
- This demo uses ccxt and public endpoints; if you add API keys, keep them secret (use Render's environment secrets).
- For production, replace in-memory HISTORY with a persistent DB (Postgres) and add authentication.
- Test with small steps; do not enable auto-ordering without thorough checks.

## Local run (Docker)
```
docker build -t futures-signal-app .
docker run -p 10000:10000 -e SYMBOL=SOL/USDT futures-signal-app
# then open http://localhost:10000/frontend/index.html
```

