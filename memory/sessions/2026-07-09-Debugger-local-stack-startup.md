<!--
Purpose:        Archived session handoff
Owner:          Debugger
Update Trigger: Session closeout archive
Harness Version: 1.1
-->

# Session Archive - Debugger Local Stack Startup

## Session Info

- **Date**: 2026-07-09
- **Agent Role**: Debugger
- **Session Goal**: Start and verify the local stack; later add the needed
  Postgres compatibility dependency, update docs, and restart the backend.
- **Branch**: `review/TASK-016-report-display-ui-review`

## Summary

- Confirmed `backend/.env` exists without printing its contents.
- Started FastAPI at `http://127.0.0.1:8000`.
- Started Vite at `http://127.0.0.1:5173`.
- Opened the app in the in-app browser.
- Verified dashboard, detail, categories, issues, and report fallback paths.
- Confirmed Supabase direct URL parsing now reaches a valid host/port shape.
- Added `psycopg2-binary==2.9.10` so provider-copied `postgresql://...` URLs
  work with SQLAlchemy.
- Updated dependency/setup docs and recorded ADR-023.
- Restarted the backend after installing the dependency. Current FastAPI PID:
  `65641`.
- Updated `ISS-002`: direct Supabase host DNS now resolves, but local routing
  to its IPv6 address fails, so the backend continues serving the documented
  static fallback data until the Supabase pooler URL is used.
- Rechecked `backend/.env` after a pooler edit attempt. The pooler URL is not
  currently assigned to a `DATABASE_URL=` key and is joined to `CORS_ORIGINS`
  text on the same line, so the backend does not load a database URL.
- Restarted the backend again with the current env state. Current FastAPI PID:
  `78058`; API is healthy but still serving static fallback data.
- With user confirmation, fixed the malformed `backend/.env` line by adding
  the missing `DATABASE_URL=` key to the bare pooler URL without printing the
  secret value.
- Confirmed `DATABASE_URL` now parses correctly and read-only `select 1`
  connectivity succeeds through the Supabase pooler.
- Restarted the backend again. Current FastAPI PID: `87346`.
- Recorded `ISS-003`: the DB connection succeeds, but required application
  tables such as `market_snapshots` are not present yet, so the API serves the
  documented static fallback data.
- With explicit user approval, applied
  `backend/migrations/001_initial_schema.sql` to the configured development
  Supabase DB and recorded ADR-024.
- Confirmed expected app tables and `pgcrypto` are present. All app tables are
  currently empty, so the API still serves the documented static fallback data.

## Verification

- `pip install psycopg2-binary==2.9.10` succeeded.
- `pip check` returned no broken requirements.
- Import check confirmed `psycopg`, `psycopg2`, and `sqlalchemy` are installed.
- Read-only DB connectivity check loads the driver, then fails on direct
  Supabase IPv6 route with `No route to host`.
- `GET http://127.0.0.1:8000/api/health` returned `status: ok`.
- `GET http://127.0.0.1:5173/` returned HTTP `200`.
- `GET http://127.0.0.1:5173/api/issues?limit=2` returned fallback issues.
- `GET http://127.0.0.1:5173/api/categories` returned sample categories.
- First issue report endpoint returned the fallback success report.
- Browser console error check returned no errors.
- `backend/.venv/bin/pytest backend/tests/test_health.py` returned 2 passed.
- `git diff --check` passed.
- Latest restart verification: backend PID `78058`, frontend PID `25166`,
  health endpoint OK, issue list available through both backend and Vite proxy.
- Latest DB verification: pooler `DATABASE_URL` parses, DNS succeeds, and
  read-only `select 1` succeeds.
- Latest restart verification: backend PID `87346`, frontend PID `25166`,
  health endpoint OK, issue list available through both backend and Vite proxy.
- Schema verification: `pgcrypto` present; `markets`, `market_outcomes`,
  `market_snapshots`, `market_metrics`, `issue_signals`, `ai_reports`,
  `related_events`, and `data_collection_logs` present with 0 rows.

## Notes

- Secret values were not printed.
- No deployment, migration, DB write, schema change, or paid API call was
  performed.
- To use live Supabase data locally, run the approved seed/collector path
  against the development DB so `market_snapshots` and related rows exist.
