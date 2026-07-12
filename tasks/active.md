<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-13_

## In Progress

TASK-099 records the user-directed v7 planning reset: positive-first prompts,
button-triggered cache-backed briefing generation, independent broad context
collection with simpler evidence levels, flexible broad-section output, and a
historical v1-v6 archive followed by separately approved cleanup.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-128 | Implement and evaluate the tool-free scenario writer | Data/AI / Backend | Data/AI Implementer | `data-ai/TASK-128-scenario-writer` | in_progress |
| TASK-122 | Consolidate project documentation phases 1-7 | PM / Reviewer | PM / Planner | `pm/TASK-122-document-consolidation` | review |
| TASK-109 | Remove superseded v1-v6 runtime code after v7 acceptance | Reviewer / Implementers | Reviewer | `review/TASK-109-legacy-report-cleanup` | assigned |

TASK-101~108 and the user-directed TASK-110~111 follow-ups are complete under the
user's approval of TASK-099 items 1-7.
TASK-112 is complete under the user's explicit approval of the v8 prompt,
public API, Frontend, and policy transition. V7 code and stored rows remain;
TASK-109 deletion is still separately gated.
TASK-113 completed the explicitly approved v8 source-retrieval improvement
without weakening URL provenance, publisher identity, excerpt support,
contradiction handling, source-parent linkage, or the no-causal-inference
boundary. Deployment, production writes, new dependencies, and legacy
deletion remained outside this work.
TASK-108 did not accept the first v7 policy after eight bounded calls produced
zero valid reports. TASK-111 removed numeric-token blocking at the user's
direction and produced the first valid development v7 report. TASK-109 may
audit cleanup candidates. On 2026-07-12 the user approved and the Reviewer
completed only the configured `ENV=local` stored-data cleanup: 241 v1-v7
reports, 10 v7 requests, and 38 cascading events were removed while all v8
rows remained. Historical compatibility/runtime-code removal remains assigned
and was not implied by that database-specific approval.

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
