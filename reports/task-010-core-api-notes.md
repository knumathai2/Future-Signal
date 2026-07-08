# TASK-010 Implementation Notes — Core Read API

_Date: 2026-07-08_
_Branch: `backend/TASK-010-core-api`_

## What changed

- `app/db/queries.py` (new): read-only SQLAlchemy helpers for the latest
  `market_snapshots`/`market_metrics` row per market, tracked
  `market_outcomes`, `issue_signals`, and `related_events`.
- `app/api/routes/issues.py`: `/api/issues`, `/api/issues/{id}`, and
  `/api/issues/{id}/history` now read through `app.db.session.get_db()`
  instead of returning the hardcoded sample dict unconditionally.
  `/api/issues/{id}/report` is unchanged (TASK-015 scope).
- No changes to `app/schemas/issues.py` field names/types, route paths, or
  query-param validation.

## Fallback strategy actually used

As of this implementation, `data-ai/TASK-007-fetch-normalize` and
`data-ai/TASK-008-snapshot-metrics` had not started (no branches, no data),
and no local `DATABASE_URL` was configured either. Per the Day 2 handoff
notes in `tasks/active.md`, this was implemented as a live-path-first design
with an explicit, logged fallback rather than waiting idle:

1. If `DATABASE_URL` is unset, or a live query raises, or `market_snapshots`
   has zero rows, the routes serve the same static sample dataset they
   returned before this task (renamed `_FALLBACK_ISSUES`), with the same
   `data_as_of` timestamp as before.
2. Every time this happens, `app.api.routes.issues` logs
   `logger.warning("FALLBACK: ...")` with a specific reason (no
   `DATABASE_URL`, query error, or empty snapshot table) — this is the
   "visible fallback marker" required by TASK-010's DoD; it is intentionally
   *not* added as a response field, since that would change the locked
   response contract.
3. Once `TASK-008` produces real `market_snapshots`/`market_metrics` rows
   against a configured database, the live path takes over automatically —
   no code change needed, verified via `tests/test_issues_live.py` against
   an in-memory SQLite fixture standing in for a real Postgres instance
   (schema itself is still not applied to any shared/production DB, per
   `AGENTS.md`).
4. A market only becomes servable once it has both a snapshot (for
   `current_value`) and a tracked outcome (for `outcome_label`) — missing
   either excludes the market rather than fabricating a value. Missing
   `change_24h`/`change_7d`/`heat_score` instead becomes `None` +
   `confidence_level="insufficient_data"`, per the no-fabrication rule.
5. Chose `200` + static fallback over Technical Design §5's `503` option
   for the "no live data" case, so the dashboard never has to render a hard
   error during a demo — see `API_CONTRACT.md` Error shape section and
   the new ADR-013 in `memory/decisions.md`.

## Public-path wording review

- Grepped `app/api` and `app/db` for the banned-phrase list
  (`memory/glossary.md`) — no matches (comments, log messages, or field
  values).
- `related_events` continue to require a non-null `event_date` before being
  surfaced; undated candidates are skipped rather than asserting a date.
- `/openapi.json` path-name check (`test_public_paths_never_use_market_terminal_vocabulary`)
  still passes unchanged.

## Known pre-existing discrepancy noted, not fixed

`API_CONTRACT.md` said invalid `window`/`sort` returns `400`; the actual
(unchanged) FastAPI `Query(pattern=...)` validation returns `422`. This
predates TASK-010 and is out of scope to "fix" here since it would require
adding a custom exception handler — a broader behavior change than "read
path only." Documented in `API_CONTRACT.md` and `memory/known-issues.md`.

## Tests

- `tests/test_issues_live.py` (new): live-path list/detail/history, unknown
  id → 404, missing-metric → null fields + `insufficient_data`, empty DB →
  fallback, invalid `sort` → 422. Uses an in-memory SQLite DB
  (`tests/conftest.py`) with two dialect-only `@compiles` shims (JSONB → a
  SQLite `JSON` column, and Postgres `UUID` forced to `CHAR(32)` so it
  doesn't get miscoerced by SQLite's numeric type affinity) — test-only,
  does not touch `app/db/models.py` or the Postgres migration.
- `tests/test_issues_contract.py` (pre-existing): unchanged and still
  passing — it never sets `DATABASE_URL`, so it continues to exercise the
  fallback path exactly as before.
- `ruff check .` and `pytest` both pass locally (17 tests).
