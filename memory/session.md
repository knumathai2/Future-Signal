<!--
Purpose:        Current session state — context handoff among agents
Owner:          Currently active agent
Update Trigger: Read at session start; must update before session ends
Harness Version: 1.1
-->

# Current Session — Outlook Signals

> After this session, copy this file to `memory/sessions/YYYY-MM-DD-[ROLE].md`.

---

## Session Info

- **Date**: 2026-07-09
- **Agent Role**: Backend Implementer
- **Session Goal**: `TASK-035` — verify `/api/issues/{id}` and
  `/api/issues/{id}/history` are ready for the Day 3 detail/chart/marker
  path, and strengthen test coverage for live-read, fallback, unknown-id,
  and history-query-failure paths.
- **Branch**: `backend/TASK-035-detail-history-readiness`

## Previous Session Summary

The prior PM session (`TASK-034`) opened Day 3 active work
(`TASK-013`, `TASK-014`, `TASK-017`, `TASK-035`, `TASK-036`) in
`tasks/active.md` and recorded the sequencing/guardrails in
`reports/day-3-work-allocation.md` (ADR-017). `TASK-035` was handed to
Backend Implementer to verify the merged `TASK-010` read path is sufficient
for Frontend's `TASK-013` chart work before any new contract work is
considered.

## Current Work

- [x] Read `AGENTS.md`, PRD, Technical Design (`docs/tech-design/README.md`
      + `03-api-and-batch-pipeline.md` §5), `memory/project.md`,
      `memory/session.md`, `tasks/active.md`,
      `reports/day-3-work-allocation.md`, and
      `prompts/implementation-backend.md`.
- [x] Local `main` was 17 commits behind `upstream/main` (missing Day 2
      closeout, TASK-033 Korean localization, ISS-001 chart-history fix, and
      all of TASK-034's Day 3 allocation); fast-forwarded before branching so
      `tasks/active.md`/`reports/day-3-work-allocation.md` reflected the real
      current state instead of stale Day 2 content.
- [x] Created branch `backend/TASK-035-detail-history-readiness` from the
      updated `main`.
- [x] Read `app/api/routes/issues.py`, `app/db/queries.py`,
      `app/schemas/issues.py`, both existing test files, and the frontend
      consumers (`IssueDetail.tsx`, `IssueTrendChart.tsx`, `App.tsx`,
      `utils/format.ts`) to confirm what the Day 3 chart/tooltip/marker path
      actually reads from the API before concluding whether a contract
      change was needed.
- [x] Verified the contract is sufficient as-is - no response-shape change
      requested or made (see Verification below for reasoning).
- [x] Added 8 new/strengthened backend tests across
      `backend/tests/test_issues_live.py` and
      `backend/tests/test_issues_contract.py`; no production code changed.
- [x] Moved `TASK-035` from `tasks/active.md` to `tasks/completed.md`.

## Completed This Session

- [x] Confirmed `/api/issues/{id}` already returns `signals`,
      `related_events`, and all core metric fields (`current_value`,
      `change_24h`, `change_7d`, `confidence_level`, `heat_score`) needed by
      the detail/chart/marker path - strengthened
      `test_get_issue_detail_live_data` to assert the full field set
      (previously only checked `signal_type` and presence of one related
      event) instead of adding a new endpoint or field.
- [x] Confirmed `/api/issues/{id}/history` filters and orders points
      correctly per requested window - added
      `test_history_multiple_snapshots_filtered_and_sorted_by_window`,
      the first test in this repo to seed >1 snapshot per market and assert
      that 24h/7d/30d windows each return the right subset in ascending
      `captured_at` order (prior tests only ever exercised the single-point
      case).
- [x] Closed a real fallback-path gap: `_resolve_live()`'s
      `except SQLAlchemyError` branch (triggered when `load_live_issues`
      itself raises, as opposed to the already-covered auxiliary
      signal/related-event/history query failures) had zero test coverage.
      Added 3 tests covering list/detail/history all correctly degrading to
      the static sample set when the primary live query fails.
- [x] Closed an unknown-id gap on the history route specifically: only
      `get_issue`'s 404 was tested before, not
      `get_issue_history`'s. Added both a live-mode and a static-fallback-mode
      test.
- [x] No schema change, new dependency, infrastructure change, or
      shared/production database write was made.
- [x] No public API response-shape change was made or is being requested.

## Issues Found / Decisions Made

- **No contract change needed.** The Day 3 chart/marker path
  (`IssueTrendChart.tsx`, `IssueDetail.tsx`) reads `history.points` for the
  chart line and independently derives its own inflection markers by
  diffing adjacent history points by >=5pp, rather than consuming the
  `signals` array `/api/issues/{id}` already returns. `change_30d` is
  likewise synthesized client-side from the 30d history's first point
  (`utils/format.ts::mapApiIssueDetailToFrontendIssue`), not read from a
  `change_30d` API field that doesn't exist. Both are legitimate frontend
  implementation choices against the existing contract, not evidence the
  contract is missing anything - so no approval-gated response-shape change
  was requested this session.
- **Remaining risk (flagging for `TASK-013`/`TASK-036`, not fixed here):**
  the frontend's adjacent-snapshot->5pp marker logic and the backend's
  actual `expectation_shift` signal logic (24h/7d windowed `change_24h`
  crossing +-5pp, per `app/core/signal_detection.py`) are two different
  computations that can disagree - e.g. a market with several small
  adjacent moves that sum past 5pp over a day would get a frontend-drawn
  marker with no corresponding `issue_signals` row, or vice versa. Not a
  backend contract defect (the `signals` array is correct and complete);
  worth Frontend/Data-AI reconciling which one is the source of truth for
  markers during `TASK-013`/`TASK-036`.
- **Remaining risk (latent, not exercised by any test):** `confidence_level`
  is typed as a 4-value `Literal` in `app/schemas/issues.py`, but
  `_issue_summary_from_live`/`_issue_detail_from_live` pass
  `metric.confidence_level` straight through as a raw DB string with no
  validation at the query layer. If `TASK-036` ever writes a
  `confidence_level` value outside the 4 accepted enum values (e.g. a typo),
  every route touching that market would fail Pydantic response validation
  with a 500 rather than degrading gracefully. Flagging for `TASK-036`
  review, not fixed here since it would mean touching the response schema's
  validation behavior without a concrete failing case to justify it.
- No architecture, dependency, infrastructure, deployment, public API, or
  wording-policy change was made or is being requested.

## Next Session: To-Do

1. Frontend (`TASK-013`) can proceed against the current detail/history
   contract with no backend blocker - the chart/tooltip/window/marker data
   it needs is already present and now more thoroughly tested.
2. Data/AI (`TASK-036`) should keep `confidence_level` writes restricted to
   the 4 accepted enum values (`sufficient`, `caution_low_activity`,
   `caution_high_volatility`, `insufficient_data`) given the latent
   Pydantic-validation risk noted above.
3. Whoever picks up marker-logic reconciliation (`TASK-013` or `TASK-036`)
   should decide whether the frontend should switch to consuming the
   `signals` array instead of its own adjacent-point diff, to avoid the two
   marker computations disagreeing in the demo.

## Verification

- `backend/.venv/Scripts/python.exe -m pytest tests -q` -> 62 passed (56
  baseline + 6 new test functions; one existing test also strengthened
  in place with additional assertions).
- `backend/.venv/Scripts/python.exe -m ruff check .` -> passed (whole
  backend).
- `git diff --check` -> passed, no whitespace errors.
- `git diff --stat` -> only `backend/tests/test_issues_contract.py` and
  `backend/tests/test_issues_live.py` changed; no production code, schema,
  dependency, or route file touched.
- Wording scan over the diff -> no prohibited-term hits (the one `bet`/
  `trade`/`position`/`profit` match is the pre-existing banned-word literal
  list inside an already-existing test, unchanged by this session).
- No shared/production database was written to in this session (SQLite
  in-memory fixtures only, same pattern as the existing test suite).
