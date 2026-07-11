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
| TASK-100 | Inventory active constraints and archive the v1-v6 contract map | PM / Reviewer | PM / Planner | `pm/TASK-100-ai-contract-archive` | assigned |
| TASK-101 | Finalize the positive-first v7 prompt, flexible section envelope, and A-D source-level policy | PM / Data-AI | Data/AI Implementer | `data-ai/TASK-101-v7-briefing-contract` | assigned |
| TASK-102 | Design the append-only generation-request schema, worker lease, cache fingerprint, and recovery contract | Backend | Backend Implementer | `backend/TASK-102-on-demand-request-schema` | assigned |
| TASK-103 | Implement broad context collection and lightweight evidence classification | Data/AI | Data/AI Implementer | `data-ai/TASK-103-broad-context-collection` | assigned |
| TASK-104 | Separate briefing generation from normal collection and add the on-demand generation service | Backend / Data-AI | Backend Implementer | `backend/TASK-104-on-demand-generation-service` | assigned |
| TASK-105 | Implement report generation, status, cache, and last-good public API contracts | Backend | Backend Implementer | `backend/TASK-105-on-demand-report-api` | assigned |
| TASK-106 | Add the explicit briefing button and flexible report/source states | Frontend | Frontend Implementer | `frontend/TASK-106-on-demand-briefing-ui` | assigned |
| TASK-107 | Review cache, concurrency, evidence, copy, and failure behavior | Reviewer | Reviewer | `review/TASK-107-v7-integration-review` | assigned |
| TASK-108 | Run a bounded development v6-v7 quality and cost comparison | Data/AI / Reviewer | Data/AI Implementer | `data-ai/TASK-108-v7-development-evaluation` | assigned |
| TASK-109 | Remove superseded v1-v6 runtime code after v7 acceptance | Reviewer / Implementers | Reviewer | `review/TASK-109-legacy-report-cleanup` | assigned |

No v7 implementation task is currently in progress. TASK-100 may start after
the TASK-099 planning packet is accepted. TASK-101 requires explicit wording
and AI-policy approval. TASK-102 requires schema approval. TASK-104 requires
workflow/runtime approval. TASK-105 requires public API approval. TASK-103 and
TASK-108 require bounded provider-call and local/development-write approval.

Deployment and production writes remain outside the approved program.

The binding proposed sequence, acceptance criteria, and approval packet are in
`reports/task-099-on-demand-briefing-policy-reset.md`. Only one task may be
`in_progress` at a time. Existing v6 worktree changes must be preserved until
TASK-100 records their archive or supersession state.

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
