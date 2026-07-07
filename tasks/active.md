<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-07_

## In Progress

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| — | (none — PM pulls assigned work from `backlog.md` at Day 1 kickoff) | — | — | — | — |

## Status Values

`assigned` | `in_progress` | `blocked` | `review` | `completed`

## Row Examples

These rows show the required format only. Do not treat them as active assignments unless the PM moves them into `In Progress`.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-006 | Finalize MVP scope doc + prohibited-wording policy | PM | PM / Planner | `pm/TASK-006-scope-lock` | assigned |
| TASK-005 | Wireframe dashboard/detail screens; start UI against dummy JSON | Frontend Implementer | Frontend Implementer | `frontend/TASK-005-dashboard-skeleton` | assigned |
| TASK-010 | Core read API endpoints | Backend Implementer | Backend Implementer | `backend/TASK-010-core-api` | assigned |
| TASK-004 | Polymarket Gamma/CLOB live spike; confirm field structure and limits | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-004-polymarket-spike` | assigned |
| TASK-018 | Copy/wording lint pass across all UI strings | PM | Reviewer | `review/TASK-018-copy-lint` | assigned |
| ISS-001 | Investigate API failure path | Debugger | Debugger | `debug/ISS-001-api-failure` | assigned |

## Task Detail Template

```
### TASK-XXX: [Title]
- **Owner**: [PM | Frontend Implementer | Backend Implementer | Data/AI Implementer]
- **Assignee**: [PM / Planner | Frontend Implementer | Backend Implementer | Data/AI Implementer | Reviewer | Debugger]
- **Branch**: [role-prefix]/[TASK-ID]-[short-kebab-slug]
- **Status**: assigned | in_progress | blocked | review | completed
- **Priority**: High | Medium | Low
- **Day**: Day [1-5]
- **Description**:
- **Definition of Done**:
  - [ ] [Condition 1]
  - [ ] [Condition 2]
```
