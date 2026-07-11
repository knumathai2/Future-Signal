<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-11_

## In Progress

ADR-048 records the user's approval for the sequential TASK-075~081 richer
narrative-summary and verified-source-link program. Existing evidence,
wording, no-causality, fail-closed, local/development-only write, and USD 100
program boundaries remain in force. Deployment and production writes remain
excluded.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-076 | Build the evidence-bounded narrative AI generator and quality gates | Data/AI | Data/AI Implementer | `data-ai/TASK-076-narrative-summary-generator` | in_progress |

Exact dependencies, ownership, acceptance criteria, handoffs, and stop
conditions are binding in
`reports/task-075-narrative-summary-source-program.md`. Only one task may be
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
