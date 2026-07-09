<!--
Purpose:        Current session state - context handoff among agents
Owner:          Currently active agent
Update Trigger: Read at session start; must update before session ends
Harness Version: 1.1
-->

# Current Session - Outlook Signals

> After this session, copy this file to `memory/sessions/YYYY-MM-DD-[ROLE].md`.

---

## Session Info

- **Date**: 2026-07-09
- **Agent Role**: Debugger
- **Session Goal**: Run the approved local/dev historical seed path against
  the configured development DB so demo charts can use live DB-backed history.
- **Branch**: `debug/ISS-004-live-data-seed`

## Previous Session Summary

The configured development Supabase DB had already been seeded once through the
approved collector/snapshot path. `/api/issues` and the Vite proxy returned
DB-backed issue payloads, but each issue had only one snapshot point, so detail
charts still needed either more collector cycles or an explicitly approved
historical seed path.

## Current Work

- [x] Read required project context: `AGENTS.md`, PRD, Service Design, Tech
      Design, UX index, `memory/project.md`, `memory/session.md`,
      `tasks/active.md`, and Debugger/Backend/Data-AI prompts.
- [x] Confirmed current branch is `debug/ISS-004-live-data-seed`; no branch
      switch was needed.
- [x] Added `backend/app/core/historical_seed.py`:
      local/dev-only CLI guard, CLOB price-history parsing/fetching, duplicate
      snapshot timestamp skipping, append-only snapshot insertion, fresh metric
      insertion, existing expectation-shift detection, and collection-log audit
      row creation.
- [x] Added `backend/tests/test_historical_seed.py` covering guard behavior,
      CLOB history parsing, existing-current-snapshot recomputation, new-market
      seeding, signal handoff, collection logging, and idempotent reruns.
- [x] Documented the command and safety boundaries in `backend/README.md`.
- [x] Recorded ADR-025 and updated architecture/project/known-issue memory.
- [x] Confirmed `ENV=local`, `DATABASE_URL` is set, and the configured DB host
      class is Supabase without printing secrets.
- [x] Ran the guarded historical seed command twice:
      first with the default `1w` interval, then with `--interval 1m` so 7d
      chart and metric windows have baseline coverage.
- [x] Verified DB row counts, latest seed logs, metric coverage, and API
      history point counts through read-only checks.

## Files Changed

- `backend/app/core/historical_seed.py`
- `backend/tests/test_historical_seed.py`
- `backend/README.md`
- `memory/decisions.md`
- `memory/architecture.md`
- `memory/project.md`
- `memory/known-issues.md`
- `memory/session.md`
- `memory/sessions/2026-07-09-Debugger-iss-004-historical-seed-path.md`

## Issues Found / Decisions Made

- ADR-025 records the approved local/dev historical seed path.
- No schema changes, dependency changes, infrastructure changes, deployment,
  `.env` edits, paid API calls, or production DB writes were performed.
- The guarded historical seed command was run against the configured
  development DB:
  `ENV=local ./.venv/bin/python -m app.core.historical_seed --confirm-local-dev-write`
  and
  `ENV=local ./.venv/bin/python -m app.core.historical_seed --interval 1m --fidelity 60 --confirm-local-dev-write`.
- Final DB state after the two seed runs:
  `market_snapshots=33238`, `market_metrics=150`, `issue_signals=2`,
  `data_collection_logs=2`.
- Latest per-market metric coverage is demo-ready for 7d:
  `markets=62`, `change_24h=50`, `change_7d=50`;
  the remaining 12 markets are older one-point rows outside this seeded set.
- 30d full-baseline readiness is still `0` markets. API 30d history returns
  multiple DB-backed points where source history exists, but not enough to
  support a full 30d baseline claim in the demo.
- Recommended demo chart window: `7d`.
- Full backend tests fail if the local shell allows `.env`'s real
  `DATABASE_URL` to load during fallback contract tests; with
  `DATABASE_URL=` and `ENV=test`, the suite passes.

## Verification

- `./.venv/bin/python -m ruff check app/core/historical_seed.py tests/test_historical_seed.py`
  -> passed.
- `./.venv/bin/python -m pytest tests/test_historical_seed.py tests/test_snapshot_metrics.py tests/test_signal_detection.py -q`
  -> 40 passed.
- `DATABASE_URL= ENV=test ./.venv/bin/python -m pytest -q`
  -> 110 passed.
- `./.venv/bin/python -m ruff check .`
  -> passed.
- Historical seed run 1:
  `8450 snapshots`, `50 metrics`, `0 signals`, `0 skipped`, `0 failed`.
- Historical seed run 2:
  `24738 snapshots`, `50 metrics`, `2 signals`, `0 skipped`, `0 failed`.
- DB verification:
  `markets=62`, `market_snapshots=33238`, `market_metrics=150`,
  `issue_signals=2`, `data_collection_logs=2`.
- API verification for one recent issue:
  `24h_history_points=27`, `7d_history_points=171`,
  `30d_history_points=303`.
- Narrow content-safety scan of changed files found no new hard-block terms
  from the seed path itself; existing ADR/template wording still contains
  legacy internal instances such as `Trade-offs`.

## Next Session: To-Do

1. Use the `7d` chart window for the live DB-backed demo flow.
2. Avoid making a 30d baseline claim unless a later source-history run proves
   at least one issue has 30d baseline coverage.
3. Continue `TASK-019` separately for manually reviewed related-event
   candidates; this historical seed path does not add event context.
