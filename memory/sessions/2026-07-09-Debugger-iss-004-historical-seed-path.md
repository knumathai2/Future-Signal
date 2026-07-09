<!--
Purpose:        Archived session handoff
Owner:          Debugger
Update Trigger: Session close
Harness Version: 1.1
-->

# Session Archive - Debugger - ISS-004 Historical Seed Path

## Session Info

- **Date**: 2026-07-09
- **Agent Role**: Debugger
- **Session Goal**: Add an approved local/dev historical seed path so demo
  charts can use live DB-backed history without fabricating points or changing
  schema/API contracts.
- **Branch**: `debug/ISS-004-live-data-seed`

## Summary

The configured development DB already had one live collector snapshot/metric row
per normalized issue, which made issue list payloads DB-backed but left detail
charts sparse. This session added a guarded historical seed module and tests,
then documented the command and recorded ADR-025.

## Work Completed

- Added `backend/app/core/historical_seed.py` with:
  - local/dev-only write guard requiring `--confirm-local-dev-write`
  - CLOB price-history parsing/fetching
  - duplicate snapshot timestamp skipping
  - append-only `market_snapshots` insertion
  - fresh latest `market_metrics` insertion
  - existing expectation-shift detection handoff
  - `data_collection_logs` audit row creation
- Added `backend/tests/test_historical_seed.py`.
- Documented the command in `backend/README.md`.
- Updated `memory/decisions.md`, `memory/architecture.md`,
  `memory/project.md`, and `memory/known-issues.md`.

## Verification

- `./.venv/bin/python -m ruff check app/core/historical_seed.py tests/test_historical_seed.py`
  -> passed.
- `./.venv/bin/python -m pytest tests/test_historical_seed.py tests/test_snapshot_metrics.py tests/test_signal_detection.py -q`
  -> 40 passed.
- `DATABASE_URL= ENV=test ./.venv/bin/python -m pytest -q`
  -> 110 passed.
- `./.venv/bin/python -m ruff check .`
  -> passed.

## Notes

- The historical seed command was not run against the configured DB in this
  session.
- No schema changes, dependency changes, infrastructure changes, deployment,
  `.env` edits, paid API calls, or production DB writes were performed.
- Full backend tests need `DATABASE_URL=`/`ENV=test` in this local environment
  when testing static fallback contracts, because `.env` contains a real DB URL.
