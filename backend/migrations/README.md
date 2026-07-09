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

Once approved, running it against a real Postgres instance is:

```bash
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
```

`psql` expects a plain Postgres URL such as `postgresql://...`; if local API
runtime uses a SQLAlchemy-specific URL like `postgresql+psycopg://...`, convert
only the scheme back to `postgresql://...` before invoking `psql`.
