<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-08_

## In Progress

No active implementation tasks are currently assigned. Day 2 is closed as of
2026-07-08; the PM should open Day 3 tasks before the next implementation
session starts.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| — | — | — | — | — | — |

All completed Day 1 and Day 2 tasks are archived in `tasks/completed.md`.

## Day 3 Handoff Notes

- **PM / Planner** should open the Day 3 terminology/disclaimer task before
  copy changes begin. Do not change the wording policy itself without human
  approval.
- **Frontend Implementer** should treat the existing dashboard-to-detail/chart
  path as the baseline and focus Day 3 work on detail/chart/tooltip polish.
- **Backend Implementer** should continue from the merged `TASK-010` read path.
  Applying the draft schema to any shared or production database still requires
  separate human approval under `AGENTS.md`.
- **Data/AI Implementer** should add inflection-point markers and
  interpretation-caution logic without expanding into P1 volatility/attention
  metrics unless PM explicitly reassigns scope.
- **Reviewer / Debugger** stay embedded. Any user-facing copy changed during
  Day 3 must pass the project wording lint before review.

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
