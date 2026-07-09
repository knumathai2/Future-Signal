<!--
Purpose:        Quick-reference commands for each agent role
Owner:          Backend Implementer
Update Trigger: New commands added, environment changed
Harness Version: 1.1
-->

# commands.md — Outlook Signals Quick Reference

_Last updated: 2026-07-09_

Monorepo layout assumed: `/frontend` (React + Vite + TS + Tailwind + Recharts), `/backend` (FastAPI + batch collector, Python).

## Setup

```bash
# Frontend
cd frontend && npm install

# Backend
cd backend && pip install -r requirements.txt

# Both
cp .env.example .env     # Configure Polymarket/DB/LLM API keys
```

Supabase dashboard connection strings usually start with `postgresql://` and
are accepted by the backend. `postgresql+psycopg://` is also supported for the
explicit psycopg3 driver path.

## Development

```bash
# Frontend (from /frontend)
npm run dev              # Start Vite dev server
npm run lint             # Lint
npm run format           # Format
npm run typecheck        # TypeScript check

# Backend (from /backend)
uvicorn app.main:app --reload    # Start FastAPI dev server
python -m batch.collector        # Run one batch collection cycle manually
ruff check .                     # Lint
ruff format .                    # Format
```

## Build & Deploy

```bash
# Frontend
npm run build             # Vite production build → deployed to Vercel on git push

# Backend
# Deployed to Railway/Render on git push (no separate build step for FastAPI)

# ⚠️ Production deploy: HUMAN APPROVAL required
```

## Database

```bash
# Run from /backend, against Supabase/Neon connection string in .env
alembic upgrade head       # Run migrations (or equivalent SQL migration tool chosen on Day 1)
python -m batch.seed        # Seed sample/demo data (fallback JSON per PRD §9.4)
# ⚠️ DB reset: development/staging environment only, never production
```

## Batch Collector (scheduled)

```bash
# Local manual run
python -m batch.collector

# Scheduled via GitHub Actions workflow (.github/workflows/collect.yml) — every 1–4h per Technical Design §6
```
