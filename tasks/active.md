<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-11_

## In Progress

ADR-038 records the user's policy, schema, API, OpenRouter budget, and
local/development-write approval for the sequential TASK-056~065 program.
Deployment and production-database writes remain excluded.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-062 | Serve the v4 context/report API | Backend Implementer | Backend Implementer | `backend/TASK-062-context-report-api` | in_progress |
| TASK-063 | Build the change-episode UI | Frontend Implementer | Frontend Implementer | `frontend/TASK-063-change-episode-ui` | assigned |
| TASK-064 | Review the automated-context integration | Reviewer | Reviewer | `review/TASK-064-auto-context-integration` | assigned |
| TASK-065 | Run local/dev backfill and record demo evidence | Data/AI Implementer + PM | Data/AI Implementer + PM / Planner | `data-ai/TASK-065-context-backfill` | assigned |

Exact dependencies, file ownership, acceptance criteria, verification commands,
handoffs, and stop conditions are binding in
`reports/task-055-automated-context-execution-plan.md`. Only one task may be
`in_progress` at a time; each successor starts from the verified predecessor.

## Status Values

`assigned` | `in_progress` | `blocked` | `review` | `completed`

## Row Examples

These rows show the required format only. Do not treat them as active
assignments unless the PM moves them into `In Progress`.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-XXX | Example PM task | PM | PM / Planner | `pm/TASK-XXX-example-task` | assigned |
| TASK-YYY | Example frontend task | Frontend Implementer | Frontend Implementer | `frontend/TASK-YYY-example-task` | assigned |
| TASK-ZZZ | Example backend task | Backend Implementer | Backend Implementer | `backend/TASK-ZZZ-example-task` | assigned |
| ISS-XXX | Example debugging task | Debugger | Debugger | `debug/ISS-XXX-example-issue` | assigned |

## Task Detail Template

```text
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
