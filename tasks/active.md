<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-08_

## In Progress

Day 1 is closed as of 2026-07-08. No Day 1 tasks remain active. Day 2 tasks should be pulled from `tasks/backlog.md` when each owner is ready to start.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| — | (none) | — | — | — | — |

`TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005`, `TASK-006`, and `TASK-011` completed 2026-07-08 — see `tasks/completed.md`.

## Day 1 Assignment Notes

- **PM / Planner** keeps Day 1 scoped to P0 kickoff work: scope lock, wording policy lock, and demo-story framing.
- **Frontend Implementer** starts from dummy JSON immediately and should not wait for the live API.
- **Backend Implementer** sequences work as scaffold and health endpoint first, then API contract and schema draft. Applying schema changes to any shared or production database still requires human approval under `AGENTS.md`.
- **Data/AI Implementer** validates Polymarket Gamma/CLOB fields and produces the 10-market sample set before `TASK-007` starts.
- **Reviewer / Debugger** are not spun up as separate Day 1 roles unless a concrete issue appears; content-safety checks stay embedded in each role's Definition of Done.

## Day 1 Closeout Checklist

| ID | Item | Blocking task | Status |
|----|------|---------------|--------|
| D1-CLOSE-001 | PM/Frontend sign-off on API contract, including the no-report-yet response shape. | `TASK-003` | closed — ADR-008 accepted |
| D1-CLOSE-002 | DB schema draft accepted as a Day 1 artifact while remaining unapplied until separate human approval. | `TASK-002` | closed — ADR-011 accepted |
| D1-CLOSE-003 | Move remaining Day 1 tasks to completed or document a named blocker after the two decisions above. | `TASK-002`, `TASK-003` | closed |

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
