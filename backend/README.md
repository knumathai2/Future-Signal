# Backend — Outlook Signals

FastAPI read-only REST API + batch collector (batch collector arrives with `TASK-007`).

## Setup

Use Python 3.11 for local setup on macOS arm. The pinned Postgres binary driver may not install under the system Python 3.9 runtime on this machine.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
cp .env.example .env         # fill in DATABASE_URL locally, never commit .env
```

### Supabase `DATABASE_URL`

Supabase connection strings copied from the dashboard usually start with
`postgresql://`. The backend now supports that form through `psycopg2-binary`.
The existing SQLAlchemy/psycopg3 form also remains valid:

```bash
# Supabase/dashboard-compatible form
DATABASE_URL=postgresql://USER:ENCODED_PASSWORD@HOST:5432/postgres

# psycopg3-explicit form
DATABASE_URL=postgresql+psycopg://USER:ENCODED_PASSWORD@HOST:5432/postgres
```

If the database password contains URL-reserved characters such as `@`, `#`,
`/`, `?`, `&`, `%`, or `:`, URL-encode the password before placing it in
`.env`.

If the direct Supabase host (`db.<project-ref>.supabase.co`) resolves but local
connection fails with an IPv6 routing error such as `No route to host`, switch
`DATABASE_URL` to the Supabase pooler connection string from the dashboard.

## Run

```bash
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs for OpenAPI docs
```

## Local/dev historical chart seed

After the first approved collector run, `/api/issues` can serve DB-backed rows
but `/api/issues/{id}/history` may still have only one point per issue. For a
demo that needs live DB-backed charts, use the local/dev historical seed path:

```bash
ENV=local ./.venv/bin/python -m app.core.historical_seed --confirm-local-dev-write
```

Safety boundaries:

- `DATABASE_URL` must point to an approved local/development database.
- The command refuses to write unless `ENV` is `local`, `dev`, `development`,
  or `test`, and `--confirm-local-dev-write` is present.
- It appends CLOB price-history points to `market_snapshots`; it does not alter
  existing snapshot rows or change the schema.
- It inserts fresh `market_metrics`, runs the existing expectation-shift
  detector for those metric rows, and records one `data_collection_logs` row.

Optional controls:

```bash
ENV=local ./.venv/bin/python -m app.core.historical_seed \
  --interval 1w \
  --fidelity 60 \
  --max-markets 10 \
  --confirm-local-dev-write
```

## Scheduled data + AI report batch

The combined batch links data collection, metric calculation, signal detection,
and stored AI report generation in one write path:

```bash
ENV=local ./.venv/bin/python -m app.core.scheduled_batch \
  --use-live-fetch \
  --max-samples 50 \
  --confirm-local-dev-write
```

For development/demo work against the current DB state, generate reports from
the latest existing metric run without collecting new market data:

```bash
ENV=local ./.venv/bin/python -m app.core.scheduled_batch \
  --reports-only \
  --confirm-local-dev-write
```

The GitHub Actions workflow `.github/workflows/daily-batch.yml` runs the
combined batch once every 24 hours and can also be started manually from
Actions. It expects `DATABASE_URL` and `OPENAI_API_KEY` secrets.

## Lint / Test

```bash
ruff check .
pytest
```

## Notes

- The API layer only reads from Postgres — it never calls Polymarket or an AI provider directly (see `../docs/tech-design/01-architecture-stack-overview.md` §3).
- Public route names use `issues` / `signals` / `reports` / `categories`, never `markets`/`bets`/`trades`/`positions`.
- DB schema was applied to the configured development Supabase DB on 2026-07-09 after human approval. Applying it or future schema changes to another shared/prod database still requires human approval.
