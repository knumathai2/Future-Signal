# Migrations

`001_initial_schema.sql` was the original schema draft. It was applied to the
currently configured development Supabase database on 2026-07-09 after explicit
human approval. Applying it, or any future schema change, to another shared or
production database still requires human approval (`AGENTS.md`, `TASK-002`).

Plain SQL is used deliberately instead of a migration framework (e.g.
Alembic) — the tool choice is listed as an open "Day 1" decision in
`commands.md` and hasn't been made yet; adding a migration-framework
dependency needs its own approval + decision, separate from the schema
draft itself.

`002_context_candidates.sql` is the ADR-038/TASK-057 append-only extension for
`context_candidates` and `context_collection_runs`. The user's approval covers
application only to local/development databases. Do not run it against a
production database or as part of a deployment without separate approval.
Duplicate `(market_id, episode_at, evidence_hash)` candidate inserts are
idempotent skips: the database rejects the duplicate and callers keep the
existing row. Both new tables use `ON DELETE CASCADE` with their parent market,
matching the lifecycle rule in `001_initial_schema.sql`.

Once approved, running it against a real Postgres instance is:

```bash
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
```

After the initial schema exists, an explicitly guarded local/development
application may use:

```bash
psql "$DATABASE_URL" -f migrations/002_context_candidates.sql
```

`psql` expects a plain Postgres URL such as `postgresql://...`; if local API
runtime uses a SQLAlchemy-specific URL like `postgresql+psycopg://...`, convert
only the scheme back to `postgresql://...` before invoking `psql`.
