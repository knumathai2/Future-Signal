# Day 4 Work Allocation - Outlook Signals

_Date: 2026-07-09_
_Owner: PM / Planner_
_Branch: `pm/TASK-038-day-4-allocation`_
_Git baseline: `origin/main` at `af83f7e` after fetching latest refs_

## Summary

Day 4 is assigned around one goal: complete the summary and demo flow without
expanding the hackathon MVP. Day 3 closed the detail/chart/caution path, so Day
4 should add stored template summaries, show them in the detail flow, curate
manual event candidates for the representative issues, and draft the
presentation/demo story.

The latest git baseline includes PR #28, which merged `TASK-037` Day 3
closeout. No active Day 3 work remains. The Day 4 work below opens the next
implementation sequence from `TASK-015`, `TASK-016`, `TASK-018`, and
`TASK-019`, plus two missing Day 4 execution tasks that come directly from PRD
section 14: backend report/fallback readiness and PM deck/demo draft.

## Day 4 Assignments

| ID | Owner | Branch | Status | First output needed | Handoff |
|---|---|---|---|---|---|
| TASK-038 | PM / Planner | `pm/TASK-038-day-4-allocation` | completed | Day 4 allocation, sequencing, and scope guardrails | All roles use this for Day 4 priorities |
| TASK-015 | Data/AI Implementer | `data-ai/TASK-015-template-report-generation` | assigned | Template-constrained report generator and safety filter | Feeds `TASK-039`, `TASK-016`, and `TASK-018` |
| TASK-039 | Backend Implementer | `backend/TASK-039-report-fallback-readiness` | assigned | Existing `/api/issues/{id}/report` reads latest stored successful report while preserving the accepted response shape | Feeds `TASK-016`; also addresses `TD-009`/`TD-010` demo fallback consistency |
| TASK-016 | Frontend Implementer | `frontend/TASK-016-report-display-ui` | assigned | Detail summary card consumes the report endpoint and handles not-yet-generated/error states | Needs `TASK-015`/`TASK-039` for final integration |
| TASK-019 | PM + Data/AI | `data-ai/TASK-019-curated-events` | assigned | 3-5 manually curated event candidates for representative demo issues | Feeds `TASK-016`, `TASK-018`, and `TASK-040` |
| TASK-040 | PM / Planner | `pm/TASK-040-demo-script-deck-draft` | assigned | Presentation deck outline and demo script draft to roughly 70 percent completeness | Feeds Day 5 final presentation and backup rehearsal |
| TASK-018 | PM / Planner | `pm/TASK-018-copy-lint` | assigned | Content-safety lint report across UI strings, templates, report text, event candidates, and deck/demo copy | Final Day 4 safety gate before closeout |

## Recommended Work Order

### First block

- Data/AI starts `TASK-015` with a deterministic template path and mechanical
  safety filter. No paid external provider call is allowed without separate
  human approval.
- Backend starts `TASK-039` in parallel as the report response contract is
  already accepted: preserve `IssueReportResponse | ReportNotYetGenerated`,
  replace the hardcoded sample path with latest stored successful rows when a
  database is available, and keep the neutral no-report state.
- PM starts `TASK-040` with a compact demo spine: dashboard -> detail -> chart ->
  summary -> caution/notice -> manual context candidate.

### Middle block

- Frontend starts `TASK-016` against the existing report response shape:
  success, not-yet-generated, and fetch-failure states should all keep
  data-as-of timing and interpretation-caution context near the summary area.
- PM/Data-AI complete `TASK-019` for exactly 3-5 representative issues.
  Candidates are manual context only; do not build automated matching and do
  not phrase candidates as causes.
- Backend/Data-AI pair only on storage/query boundaries already present in the
  schema. Any schema change pauses for human approval.

### Final block

- PM runs `TASK-018` after the report template, UI strings, event candidates,
  and demo script draft are available.
- Reviewer pass stays embedded. Any user-facing string changed during Day 4
  must pass the project wording lint before Day 4 closeout.
- Day 4 closes only if the Home -> Detail -> Chart -> Summary path can be
  demonstrated with either live/local data or honest fallback data.

## Day 4 Guardrails

- Do not deploy, modify infrastructure, apply the schema to a shared or
  production database, add dependencies, or change public API shapes without
  human approval.
- Do not call paid external AI APIs without human approval. The Day 4 default
  is template generation plus a safety filter, with any provider hook disabled
  or stubbed until approved.
- Do not add accounts, saved lists, notifications, scheduled reports, team
  sharing, wallet-level features, or automated event matching.
- Do not expand into P1 `/api/signals` feed, full volatility/attention scoring,
  broad UI polish, or setup documentation until the Day 4 P0 path is complete.
- Related event candidates remain manually curated context candidates for the
  demo set only.

## Acceptance Checklist

Day 4 is ready to close only when:

- Stored template summaries exist or can be generated locally for the
  representative issues without open-ended analysis.
- The report endpoint serves the latest successful stored summary when present
  and the accepted neutral empty state when absent.
- The detail summary card renders success, not-yet-generated, and error states
  without losing data-as-of timing or interpretation-caution context.
- 3-5 representative issues have manually curated event candidates, or the
  demo script explicitly avoids event-candidate sections for issues without
  them.
- The presentation/demo draft tells the product story clearly and keeps the
  scope framed as issue monitoring.
- A content-safety lint pass is recorded for changed user-facing strings,
  templates, event candidates, and demo copy.
- No P1/P2 feature has entered active scope without explicit PM assignment and
  the required human approval where applicable.

## Stretch Work

Only after the checklist above is satisfied, the team may consider the existing
P1 `TASK-025` empty/loading/error state polish or small responsive fixes that
directly improve the demo path. Do not start category/feed/extra metric work on
Day 4 unless the PM explicitly reassigns scope.
