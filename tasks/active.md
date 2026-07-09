<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-09_

## In Progress

Day 3 work is assigned. Start from `reports/day-3-work-allocation.md` and the
Day 2 baseline; keep all work inside PRD §14's detail/chart/badge scope.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-013 | Issue detail UI + Recharts line chart | Frontend Implementer | Frontend Implementer | `frontend/TASK-013-detail-chart` | assigned |
| TASK-014 | Interpretation-caution badge alignment | Frontend Implementer | Frontend Implementer | `frontend/TASK-014-caution-badges` | assigned |
| TASK-017 | Disclaimer copy, footer, and dedicated notice surface | Frontend Implementer + PM | Frontend Implementer + PM / Planner | `frontend/TASK-017-disclaimer-copy` | assigned |
| TASK-035 | Issue detail/history API readiness pass | Backend Implementer | Backend Implementer | `backend/TASK-035-detail-history-readiness` | assigned |
| TASK-036 | Caution-badge logic and expectation-shift marker handoff | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-036-caution-signal-handoff` | assigned |
| TASK-039 | Stabilize API and implement fallback data handling | Backend Implementer | Backend Implementer | `backend/TASK-039-stabilize-api-fallback` | completed |

Completed Day 1, Day 2, and PM allocation tasks are archived in
`tasks/completed.md`.

## Day 3 Handoff Notes

- **PM / Planner** completed `TASK-034` in
  `reports/day-3-work-allocation.md`. Continue as the scope gate for
  `TASK-017`; do not change the wording policy itself without human approval.
- **Frontend Implementer** should treat the existing dashboard-to-detail/chart
  path as the baseline and focus Day 3 work on detail/chart/tooltip polish,
  marker rendering, and badge placement.
- **Backend Implementer** should continue from the merged `TASK-010` read path.
  Applying the draft schema to any shared or production database still requires
  separate human approval under `AGENTS.md`.
- **Data/AI Implementer** should improve caution-level logic using the existing
  schema/API fields and avoid expanding into P1 metric families unless PM
  explicitly reassigns scope.
- **Reviewer / Debugger** stay embedded. Any user-facing copy changed during
  Day 3 must pass the project wording lint before review.

## Active Task Details

### TASK-013: Issue detail UI + Recharts line chart
- **Owner**: Frontend Implementer
- **Assignee**: Frontend Implementer
- **Branch**: `frontend/TASK-013-detail-chart`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 3
- **Description**: Finish the issue detail chart experience against the current
  `/api/issues/{id}` and `/api/issues/{id}/history` contract, including window
  selection, tooltip values, marker rendering, and insufficient-history states.
- **Definition of Done**:
  - [ ] Dashboard -> detail -> chart works with API data and static fallback.
  - [ ] 24h, 7d, and 30d windows render either a usable line or a clear
        insufficient-history state.
  - [ ] Tooltip text shows timestamp and reflected expectation value without
        outcome or cause claims.
  - [ ] Expectation-shift markers match the accepted 5pp threshold logic or
        the API-provided signal rows.
  - [ ] Frontend `typecheck`, `lint`, and `build` pass.

### TASK-014: Interpretation-caution badge alignment
- **Owner**: Frontend Implementer
- **Assignee**: Frontend Implementer
- **Branch**: `frontend/TASK-014-caution-badges`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 3
- **Description**: Audit and align the reusable caution badge across dashboard
  cards, detail header, chart area, and summary area so each supported caution
  level is visible and consistently worded.
- **Definition of Done**:
  - [ ] `sufficient`, `caution_low_activity`, `caution_high_volatility`, and
        `insufficient_data` all have safe labels and detail copy.
  - [ ] Badge placement stays near the metric it qualifies on every major
        data-bearing screen.
  - [ ] Visual treatment stays neutral and does not mimic transactional UI
        patterns.
  - [ ] Changed user-facing strings pass the project wording scan.

### TASK-017: Disclaimer copy, footer, and dedicated notice surface
- **Owner**: Frontend Implementer + PM
- **Assignee**: Frontend Implementer + PM / Planner
- **Branch**: `frontend/TASK-017-disclaimer-copy`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 3
- **Description**: Place short caution/disclaimer copy on the dashboard and
  detail flow, retain the footer reminder, and provide one dedicated notice
  surface without changing the approved wording policy.
- **Definition of Done**:
  - [ ] PM-approved short caution copy appears near data-heavy detail content.
  - [ ] Footer copy appears on all major screens.
  - [ ] Dedicated notice surface exists without adding accounts, routing
        dependencies, notifications, or other excluded features.
  - [ ] No wording-policy changes are made without human approval.
  - [ ] Changed user-facing strings pass the project wording scan.

### TASK-035: Issue detail/history API readiness pass
- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-035-detail-history-readiness`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 3
- **Description**: Verify that the accepted detail and history endpoints
  provide the frontend with enough data for the Day 3 chart, tooltip, and
  expectation-shift marker experience while preserving accepted response
  shapes.
- **Definition of Done**:
  - [ ] `/api/issues/{id}` returns detail fields, related-event candidates,
        and expectation-shift rows when available.
  - [ ] `/api/issues/{id}/history` returns ordered points for the requested
        window and keeps the honest fallback behavior for missing history.
  - [ ] Backend tests cover live-read, fallback, unknown-id, and history-query
        failure cases relevant to the chart path.
  - [ ] No public API response-shape change is made without human approval.

### TASK-036: Caution-badge logic and expectation-shift marker handoff
- **Owner**: Data/AI Implementer
- **Assignee**: Data/AI Implementer
- **Branch**: `data-ai/TASK-036-caution-signal-handoff`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 3
- **Description**: Extend MVP caution-level population using existing
  `market_metrics.confidence_level` values and document how the 5pp
  expectation-shift rows should be consumed by backend/frontend marker logic.
- **Definition of Done**:
  - [ ] `TD-008` is addressed for the MVP path without adding schema fields.
  - [ ] Low-activity and high-volatility caution levels use conservative,
        documented thresholds based on available sample data.
  - [ ] Markets with insufficient history still produce `insufficient_data`
        rather than fabricated movement values.
  - [ ] Expectation-shift handoff notes match the existing
        `issue_signals` payload and the frontend marker behavior.
  - [ ] Backend metric/signal tests are added or updated for the new caution
        logic.

### TASK-039: Stabilize API and implement fallback data handling
- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-039-stabilize-api-fallback`
- **Status**: completed
- **Priority**: High
- **Day**: Day 4
- **Description**: Stabilize the core API and ensure robust fallback data handling so the application does not crash during the demo if data is missing or systems fail.
- **Definition of Done**:
  - [x] Fallback logic is implemented for missing history, timeouts, and unknown IDs.
  - [x] Backend tests are added or updated to cover these failure and fallback scenarios.
  - [x] The API contract remains unchanged, and the frontend demo flow is fully supported.

## Status Values

`assigned` | `in_progress` | `blocked` | `review` | `completed`

## Row Examples

These rows show the required format only. Do not treat them as active assignments unless the PM moves them into `In Progress`.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-XXX | Example PM task | PM | PM / Planner | `pm/TASK-XXX-example-task` | assigned |
| TASK-YYY | Example frontend task | Frontend Implementer | Frontend Implementer | `frontend/TASK-YYY-example-task` | assigned |
| TASK-ZZZ | Example backend task | Backend Implementer | Backend Implementer | `backend/TASK-ZZZ-example-task` | assigned |
| ISS-XXX | Example debugging task | Debugger | Debugger | `debug/ISS-XXX-example-issue` | assigned |

## Task Detail Template

```
### TASK-XXX: [Title]
- **Owner**: [PM | Frontend Implementer | Backend Implementer | Data/AI Implementer]
- **Assignee**: [PM / Planner | Frontend Implementer | Backend Implementer | Data/AI Implementer]
- **Branch**: [role-prefix]/[TASK-ID]-[short-kebab-slug]
- **Status**: assigned | in_progress | blocked | review | completed
- **Priority**: High | Medium | Low
- **Day**: Day [1-5]
- **Description**:
- **Definition of Done**:
  - [ ] [Condition 1]
  - [ ] [Condition 2]
```
