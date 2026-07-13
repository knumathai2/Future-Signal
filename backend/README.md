# Backend — Outlook Signals

FastAPI issue-data API + append-only v8 generation requests + batch collector.

TASK-117 adds validated-block SSE delivery. The worker emits one NDJSON writer
response, persists only complete blocks that pass the active v8 gates, and the
API replays them from
`GET /api/issues/{id}/report/requests/{request_id}/stream`. Migration 005 must
exist in the target database before this path is enabled. It was subsequently
applied only to the explicitly approved `ENV=local` development database;
other environments remain separately gated.

TASK-126 adds a default-off, local/development-only scenario-session API and
migration 006, applied only to the approved local DB. Setting
`SCENARIO_CONVERSATION_ENABLED=true` exposes
capability-authenticated session/turn/request storage and validated-block
replay. TASK-132 starts the existing isolated worker after a newly created turn
commits, while the API process itself never constructs a provider client.
Idempotent replay does not launch a second worker. The feature remains
unavailable outside `ENV=local` or `ENV=development`. Migration 006 must exist
before enabling the flag against a database.

TASK-128 adds the guarded local/development worker for one queued scenario
request. It can still be invoked manually for recovery:

```bash
python -m app.core.scenario_worker --request-id <uuid> --confirm-local-dev-write
```

It performs one tool-free call and stores only output that passes the complete
premise, safety, leakage, number, and restricted-Markdown gates. TASK-132 may
launch it only after a new local/development turn commits; the scheduled
collector never launches it.

TASK-134 recovers only requests that remain at `queued`, attempt zero, for at
least five seconds. Authenticated status/SSE reads may relaunch the child with a
20-second process-local cooldown and a three-launch cap; the worker serializes
claim with a database row lock before any provider call. Running and terminal
attempts are never automatically retried.

TASK-135 keeps complete validation and storage ahead of public delivery, then
paces stored scenario paragraph/list blocks over authenticated SSE. The first
block is immediate and later blocks are separated by 0.2 seconds, allowing the
Frontend to render progressively without exposing raw provider fragments. The
read transaction is released before paced network delivery.

PostgreSQL engines default to three pooled plus one overflow connection per
process (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, and `DB_POOL_TIMEOUT_SECONDS` are
optional bounded overrides). This leaves room for the API and detached worker
under small session-mode pool ceilings without modifying `.env` for local use.

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

In `ENV=local`, `ENV=dev`, or `ENV=development`, a successful queued
`POST /api/issues/{id}/report/generate` automatically starts the existing
worker as an isolated child process for that exact request. The API returns
HTTP 202 without waiting for generation and never creates a provider client.
If child-process startup fails, the committed request remains queued and can be
recovered with the manual command below:

```bash
ENV=local ./.venv/bin/python -m app.core.on_demand_worker \
  --confirm-local-dev-write
```

The v8 Frontend sends `refresh_context=true`. The child lazily builds the
bounded 90/180-day research path, checks the cumulative context reservation,
stores only accepted exact-excerpt evidence, and follows the immutable
successor request when refreshed evidence changes the input fingerprint.

Production auto-start remains disabled until a separately approved worker
deployment exists.

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

## Scheduled market-data collection

The active workflow runs market-data collection every four hours. It fetches
up to 50 active binary markets, appends current snapshots and metrics, detects
configured change signals, and records collection health. Normal collection
does not invoke context research or the briefing writer:

```bash
ENV=local ./.venv/bin/python -m app.core.scheduled_batch \
  --use-live-fetch \
  --max-samples 50 \
  --skip-ai-reports \
  --skip-context-research \
  --confirm-local-dev-write
```

The checked-in workflow is
`.github/workflows/four-hour-collection.yml`. It uses only `DATABASE_URL` and
can also be started manually from Actions. Historical `--reports-only` and v4
compatibility flags remain in the CLI for audit/development comparison but are
not part of the current v8 operating path. Paid provider evaluations, another
database, production writes, and deployment require their own approvals.

## Lint / Test

```bash
ruff check .
pytest
```

## Notes

- The API reads issue data and appends generation requests/events in Postgres.
  It never calls Polymarket or an AI provider directly (see
  `../docs/tech-design/01-architecture-stack-overview.md` §3).
- Public route names use `issues` / `signals` / `reports` / `categories`, never `markets`/`bets`/`trades`/`positions`.
- DB schema was applied to the configured development Supabase DB on 2026-07-09 after human approval. Applying it or future schema changes to another shared/prod database still requires human approval.
