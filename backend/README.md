# Backend — Outlook Signals

FastAPI read-only REST API + batch collector (batch collector arrives with `TASK-007`).

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements-dev.txt
cp .env.example .env         # fill in DATABASE_URL locally, never commit .env
```

## Run

```bash
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs for OpenAPI docs
```

## Lint / Test

```bash
ruff check .
pytest
```

## Notes

- The API layer only reads from Postgres — it never calls Polymarket or an AI provider directly (see `../docs/tech-design/01-architecture-stack-overview.md` §3).
- Public route names use `issues` / `signals` / `reports` / `categories`, never `markets`/`bets`/`trades`/`positions`.
- DB schema is currently a draft (`migrations/`) — see `TASK-002`. It has not been applied to any database; human approval is required before doing so.
