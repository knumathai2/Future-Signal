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
- **Session Goal**: Add and run the approved local/dev historical seed path so
  demo charts can use live DB-backed history.
- **Branch**: `debug/ISS-004-live-data-seed`

## Summary

The configured development DB already had one live collector snapshot/metric row
per normalized issue, which made issue list payloads DB-backed but left detail
charts sparse. This session added a guarded historical seed module and tests,
documented the command, recorded ADR-025, and then ran the command against the
configured development DB.

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
- Ran:
  `ENV=local ./.venv/bin/python -m app.core.historical_seed --confirm-local-dev-write`.
- Ran:
  `ENV=local ./.venv/bin/python -m app.core.historical_seed --interval 1m --fidelity 60 --confirm-local-dev-write`.

## DB Result

- First seed run: `8450 snapshots`, `50 metrics`, `0 signals`, `0 skipped`,
  `0 failed`.
- Second seed run: `24738 snapshots`, `50 metrics`, `2 signals`, `0 skipped`,
  `0 failed`.
- Final counts: `markets=62`, `market_snapshots=33238`,
  `market_metrics=150`, `issue_signals=2`, `data_collection_logs=2`.
- Latest per-market metric coverage: `markets=62`, `change_24h=50`,
  `change_7d=50`.
- API verification for one recent issue: `24h_history_points=27`,
  `7d_history_points=171`, `30d_history_points=303`.
- 30d full-baseline readiness remains `0` markets; use `7d` for the demo
  chart window unless a later source-history run proves otherwise.

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

- No schema changes, dependency changes, infrastructure changes, deployment,
  `.env` edits, paid API calls, or production DB writes were performed.
- Full backend tests need `DATABASE_URL=`/`ENV=test` in this local environment
  when testing static fallback contracts, because `.env` contains a real DB URL.
