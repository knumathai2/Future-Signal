<!--
Purpose:        Archived session handoff for TASK-017 implementation
Owner:          Frontend Implementer + PM / Planner
Update Trigger: Archived from `memory/session.md` after session end
Harness Version: 1.1
-->

# Session Archive — TASK-017 Disclaimer Copy

---

## Session Info

- **Date**: 2026-07-09
- **Agent Role**: Frontend Implementer + PM / Planner
- **Session Goal**: Complete `TASK-017` by adding short caution copy, retaining
  footer reminders, and providing one dedicated information notice surface
  without changing the approved wording policy.
- **Branch**: `frontend/TASK-017-disclaimer-copy`

## Previous Session Summary

`TASK-017` preparation completed on the latest `main` baseline (`afbb2da`).
`TASK-014` had already merged the caution-badge copy and detail data-as-of
placement, leaving `TASK-017` as the final active Day 3 task.

## Current Work

- [x] Confirmed branch and task context from `AGENTS.md`, PRD/UX policy,
      `tasks/active.md`, `reports/day-3-work-allocation.md`, `standards.md`,
      and prior frontend handoff notes.
- [x] Added `frontend/src/components/InformationNotice.tsx` with shared short
      caution copy, a reusable global footer, and a dedicated in-app information
      notice screen.
- [x] Wired `Dashboard` header/footer to open the dedicated notice surface and
      replaced duplicated dashboard notice copy with the reusable short notice.
- [x] Wired `IssueDetail` metric/summary/footer areas to the reusable notice
      components while preserving issue-specific caution levels and data-as-of
      timing near the data-heavy content.
- [x] Added the `notice` screen state in `App.tsx` without a routing dependency.
- [x] Moved `TASK-017` from `tasks/active.md` to `tasks/completed.md`.
- [x] Updated `memory/project.md` with Day 3 closeout readiness.

## Completed This Session

- [x] PM-safe short caution copy appears on dashboard and near detail metric /
      summary content.
- [x] Footer reminder copy appears on dashboard, issue detail, and the dedicated
      notice surface through the shared `GlobalFooter`.
- [x] A dedicated information notice surface exists inside the app with no
      accounts, route-library dependency, notifications, public API change,
      schema change, infrastructure change, deployment, production database
      write, or wording-policy change.
- [x] `TASK-017` is completed and archived in `tasks/completed.md`.

## Issues Found / Decisions Made

- No new product, architecture, schema, dependency, infrastructure, public API,
  or wording-policy decision was made.
- No new persistent issue was added to `memory/known-issues.md`.
- Existing `TD-001` Vite/Recharts chunk-size warning remains non-blocking.
- Existing `TD-009` backend/static fallback title-language note remains open
  and was not changed by this task.

## Verification

- `npm run typecheck` in `frontend` -> passed.
- `npm run lint` in `frontend` -> passed.
- `npm run build` in `frontend` -> passed, with the existing non-blocking
  Vite/Recharts chunk-size warning tracked as `TD-001`.
- Frontend hard-block wording scan over `frontend/src` -> no hits.
- Frontend English causal-phrase scan over `frontend/src` -> no hits.
- `git diff --check` -> passed.
- Browser QA at `http://127.0.0.1:5175/?state=error`:
  - dashboard short notice, footer, and dedicated notice button present;
  - dedicated notice screen opens from dashboard and detail;
  - detail screen keeps short notice, summary notice, footer, and 7 data-as-of
    references visible in the static fallback path;
  - mobile 390px notice path has no horizontal overflow;
  - browser console error log is empty.

## Next Session: To-Do

1. Request review for `TASK-017`.
2. Start Day 4 only after PM confirms Day 3 closeout, likely with `TASK-015`
   template summary generation/display and manually curated related-event
   candidates.
