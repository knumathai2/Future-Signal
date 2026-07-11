<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-11_

## In Progress

The user-approved evidence-aware briefing objective is decomposed into
TASK-092~098 below. Existing evidence, wording, no-causality, fail-closed,
local/development-only write, and cumulative USD 100 program boundaries remain
in force. Deployment and production writes remain excluded.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-097 | Regenerate and evaluate v6 reports in development | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-097-v6-development-regeneration` | in_progress |
| TASK-098 | Review the integrated v6 flow and leave the development UI ready for user review | Reviewer | Reviewer | `review/TASK-098-evidence-aware-briefing-integration` | assigned |


TASK-092~098 must run in dependency order:

1. TASK-092 completes the four-mode policy, deterministic decision rules,
   section ownership, duplication rules, disclosure contract, and exact
   approval boundary.
2. TASK-093 starts only after TASK-092 and any required AI-policy approval.
3. TASK-094 may start after TASK-092, but workflow/runtime configuration
   changes remain separately approval-gated.
4. TASK-095 starts only after TASK-093 and explicit public API approval.
5. TASK-096 starts only after TASK-095.
6. TASK-097 starts only after TASK-093~096 and may write only append-only local
   or development records within the recorded cumulative budget.
7. TASK-098 starts only after TASK-092~097 pass their own acceptance checks.

Only one task may be `in_progress` at a time. Existing user worktree changes
from the grounding/regeneration session must be preserved. No new dependency,
schema migration, production write, deployment, or infrastructure mutation is
authorized by this task list.

Deployment and production writes remain outside the approved program.

The detailed TASK-092~098 acceptance criteria and stop conditions are binding
in the user-provided goal objective and the TASK-092 contract report once
accepted.

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
