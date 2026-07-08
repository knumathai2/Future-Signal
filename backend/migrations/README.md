# Migrations

`001_initial_schema.sql` is a **draft**. It has not been applied to any
database. Applying it to a shared or production database requires human
approval (`AGENTS.md`, `TASK-002`).

Plain SQL is used deliberately instead of a migration framework (e.g.
Alembic) — the tool choice is listed as an open "Day 1" decision in
`commands.md` and hasn't been made yet; adding a migration-framework
dependency needs its own approval + decision, separate from the schema
draft itself.

Once approved, running it against a real Postgres instance is:

```bash
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
```
