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
`TASK-013`, `TASK-014`, `TASK-035`, and `TASK-036` completed 2026-07-09 - see
`tasks/completed.md`.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-017 | Disclaimer copy, footer, and dedicated notice surface | Frontend Implementer + PM | Frontend Implementer + PM / Planner | `frontend/TASK-017-disclaimer-copy` | assigned |

Completed Day 1, Day 2, and PM allocation tasks are archived in
`tasks/completed.md`.

## Day 3 Handoff Notes

- **PM / Planner** completed `TASK-034` in
  `reports/day-3-work-allocation.md`. Continue as the scope gate for
  `TASK-017`; do not change the wording policy itself without human approval.
- **Frontend Implementer** completed `TASK-013` on
  `frontend/TASK-013-detail-chart` and `TASK-014` on
  `frontend/TASK-014-caution-badges`; continue with `TASK-017` from the
  hardened detail/chart/badge baseline.
- **Backend Implementer** completed `TASK-035`: the merged `TASK-010` read
  path already supports the Day 3 chart/marker experience, so no contract
  change was made. Applying the draft schema to any shared or production
  database still requires separate human approval under `AGENTS.md`.
- **Data/AI Implementer** completed `TASK-036`: caution-level thresholds and
  the expectation-shift marker handoff are documented in ADR-019 and archived
  in `tasks/completed.md`.
- **Reviewer / Debugger** stay embedded. Any user-facing copy changed during
  Day 3 must pass the project wording lint before review.

## Active Task Details

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
