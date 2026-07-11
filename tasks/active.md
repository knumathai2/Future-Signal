<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-11_

## In Progress

TASK-099 records the user-directed v7 planning reset: positive-first prompts,
button-triggered cache-backed briefing generation, independent broad context
collection with simpler evidence levels, flexible broad-section output, and a
historical v1-v6 archive followed by separately approved cleanup.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-105 | Implement report generation, status, cache, and last-good public API contracts | Backend | Backend Implementer | `backend/TASK-105-on-demand-report-api` | assigned |
| TASK-106 | Add the explicit briefing button and flexible report/source states | Frontend | Frontend Implementer | `frontend/TASK-106-on-demand-briefing-ui` | assigned |
| TASK-107 | Review cache, concurrency, evidence, copy, and failure behavior | Reviewer | Reviewer | `review/TASK-107-v7-integration-review` | assigned |
| TASK-108 | Run a bounded development v6-v7 quality and cost comparison | Data/AI / Reviewer | Data/AI Implementer | `data-ai/TASK-108-v7-development-evaluation` | assigned |
| TASK-109 | Remove superseded v1-v6 runtime code after v7 acceptance | Reviewer / Implementers | Reviewer | `review/TASK-109-legacy-report-cleanup` | assigned |

TASK-101~104 are complete under the user's approval of TASK-099 items 1-7.
TASK-105 is next and may change the approved
public report interface, and TASK-103/TASK-108 may use bounded provider calls
and append-only local/development writes.

Deployment and production writes remain outside the approved program.

The binding proposed sequence, acceptance criteria, and approval packet are in
`reports/task-099-on-demand-briefing-policy-reset.md`. Only one task may be
`in_progress` at a time. Existing v6 worktree changes must be preserved until
TASK-100 records their archive and supersession state in
`docs/archive/ai-report-contracts/README.md`.

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
