# Day 3 Work Allocation — Outlook Signals

_Date: 2026-07-09_
_Owner: PM / Planner_
_Branch: `pm/TASK-034-day-3-allocation`_

## Summary

Day 3 is assigned around one goal: make the detail view trustworthy and
demo-ready. The work stays inside PRD §14 Day 3: issue detail, time-series
chart, tooltip behavior, expectation-shift markers, interpretation-caution
badges, and required caution/disclaimer copy.

The Day 2 baseline is usable: normalized sample data, 24h/7d metrics,
expectation-shift detection, the core read API, and dashboard integration are
merged. Day 3 should harden the detail path rather than expand scope.

Source scope:

- PRD §14 Day 3: detail screen + chart + badges.
- Day 2 closeout: data/API/dashboard path is merged and verified.
- Known debt: `TD-008` says caution levels only distinguish
  `sufficient`/`insufficient_data`; Day 3 must resolve the MVP caution-badge
  logic without pulling in P1 metric families.
- AGENTS.md approval gates: no shared/production DB writes, dependency
  additions, public API changes, infrastructure changes, deployments, or
  wording-policy changes without human approval.

## Day 3 Assignments

| ID | Owner | Branch | Status | First output needed | Handoff |
|---|---|---|---|---|---|
| TASK-034 | PM / Planner | `pm/TASK-034-day-3-allocation` | completed | Day 3 allocation, sequencing, and scope guardrails | All roles use this for Day 3 priorities |
| TASK-013 | Frontend Implementer | `frontend/TASK-013-detail-chart` | assigned | Detail chart/tooltip pass against the current API and fallback paths | Needs `TASK-035` if history or detail data is incomplete |
| TASK-014 | Frontend Implementer | `frontend/TASK-014-caution-badges` | assigned | Badge copy/placement audit across cards, detail header, chart area, and summary area | Needs `TASK-036` for populated caution levels |
| TASK-017 | Frontend Implementer + PM | `frontend/TASK-017-disclaimer-copy` | assigned | Short caution copy, footer copy, and a dedicated notice surface without changing policy | Feeds reviewer wording pass and Day 4 deck language |
| TASK-035 | Backend Implementer | `backend/TASK-035-detail-history-readiness` | assigned | Verified detail/history responses for chart and marker consumption | Feeds `TASK-013`; must preserve accepted response shapes |
| TASK-036 | Data/AI Implementer | `data-ai/TASK-036-caution-signal-handoff` | assigned | MVP caution-level logic and expectation-shift marker handoff guidance | Feeds `TASK-014`, `TASK-035`, and Day 4 summary generation |

## Recommended Work Order

### First block

- PM completes `TASK-034` and keeps Day 3 work tied to detail/chart/badge
  readiness.
- Backend starts `TASK-035` by verifying that `/api/issues/{id}` and
  `/api/issues/{id}/history` provide enough live or fallback data for the
  chart to avoid a misleading blank state.
- Data/AI starts `TASK-036` by resolving the MVP caution-level path:
  keep issue rows visible by default, populate caution badges when the data is
  thin or too unsettled to read cleanly, and avoid adding new schema/API fields.
- Frontend starts `TASK-013` against the existing issue detail and history
  contract, keeping the current fallback behavior intact.

### Middle block

- Backend and Frontend pair on chart data shape issues only if the accepted
  contract is insufficient. Any response-shape change pauses for human
  approval.
- Data/AI implements caution-level population using existing enum values and
  records the threshold rationale in the decision log or task notes.
- Frontend completes tooltip, window selection, insufficient-history states,
  and marker rendering using either API-provided expectation-shift rows or a
  matching local 5pp history calculation.

### Final block

- Frontend runs `TASK-014` after `TASK-036` has a usable output so every caution
  state can be checked visually.
- PM and Frontend finish `TASK-017` copy placement and wording scan.
- Reviewer pass stays embedded: changed user-facing strings need the project
  wording lint, and every data-bearing surface needs data-as-of + caution text.

## Day 3 Guardrails

- Do not start `TASK-015` template report generation until the detail chart and
  caution-badge path are stable, unless PM explicitly reassigns it late in the
  day.
- Do not build category-filter expansion, a separate cross-issue feed,
  volatility/attention score surfaces, or event-candidate editing ahead of the
  Day 3 P0 path.
- Do not apply the schema draft to a shared or production database without
  separate human approval.
- Do not change the accepted public API contract without human approval.
- Do not add new dependencies, deployment config, or infrastructure work during
  Day 3 allocation.
- Related event candidates remain manual-only and must be presented as context
  candidates, not as causes.

## Acceptance Checklist

Day 3 is ready to close only when:

- The user can move from dashboard to detail without interruption.
- The chart renders a useful line when enough history exists and a clear
  insufficient-history state when it does not.
- 24h/7d/30d chart windows, tooltip values, and marker labels avoid
  overstatement.
- Caution badges render consistently for every supported caution level.
- Every data-bearing detail surface shows data-as-of timing and caution text.
- Changed user-facing strings pass the project wording scan.
- No P1/P2 feature has entered the active scope without explicit PM assignment.

## Day 4 Readiness

If Day 3 closes cleanly, Day 4 can start `TASK-015`, `TASK-016`, `TASK-018`,
and `TASK-019` in that order: template summary generation, summary display,
wording lint, and manually curated related-event candidates for the demo set.
