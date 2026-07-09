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
- **Session Goal**: Add an approved local/dev historical seed path so demo
  charts can use live DB-backed history without fabricating points or changing
  schema/API contracts.
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
- The historical seed command was not run against the configured DB in this
  session. It now exists as a guarded path for demo prep:
  `ENV=local ./.venv/bin/python -m app.core.historical_seed --confirm-local-dev-write`.
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
- Narrow content-safety scan of changed files found no new hard-block terms
  from the seed path itself; existing ADR/template wording still contains
  legacy internal instances such as `Trade-offs`.

## Next Session: To-Do

1. If the Day 4/Day 5 demo needs live DB-backed charts, run the guarded
   historical seed command only after confirming `DATABASE_URL` targets the
   approved local/development DB.
2. After running it, verify `/api/issues/{id}/history?window=7d` returns
   multiple points and that `/api/issues` surfaces fresh metric rows.
3. Continue `TASK-019` separately for manually reviewed related-event
   candidates; this historical seed path does not add event context.
