<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-08_

## In Progress

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-006 | Finalize MVP scope doc, prohibited-wording policy, and Day 1 presentation story | PM | PM / Planner | `pm/TASK-006-day-1-allocation` | in_progress |
| TASK-005 | Wireframe dashboard/detail screens; start UI against dummy JSON | Frontend Implementer | Frontend Implementer | `frontend/TASK-005-dashboard-skeleton` | assigned |
| TASK-001 | Repo scaffold: create `/frontend` and `/backend` project shells | Backend Implementer | Backend Implementer | `backend/TASK-001-repo-scaffold` | assigned |
| TASK-011 | Add `/api/health` endpoint | Backend Implementer | Backend Implementer | `backend/TASK-011-health-endpoint` | assigned |
| TASK-003 | API contract draft and response-shape agreement | Backend Implementer + PM | Backend Implementer | `backend/TASK-003-api-contract` | assigned |
| TASK-002 | DB schema draft for MVP tables | Backend Implementer | Backend Implementer | `backend/TASK-002-db-schema` | assigned |
| TASK-004 | Polymarket Gamma/CLOB live spike; confirm field structure and collect 10 sample markets | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-004-polymarket-spike` | assigned |

## Day 1 Assignment Notes

- **PM / Planner** keeps Day 1 scoped to P0 kickoff work: scope lock, wording policy lock, and demo-story framing.
- **Frontend Implementer** starts from dummy JSON immediately and should not wait for the live API.
- **Backend Implementer** sequences work as scaffold and health endpoint first, then API contract and schema draft. Applying schema changes to any shared or production database still requires human approval under `AGENTS.md`.
- **Data/AI Implementer** validates Polymarket Gamma/CLOB fields and produces the 10-market sample set before `TASK-007` starts.
- **Reviewer / Debugger** are not spun up as separate Day 1 roles unless a concrete issue appears; content-safety checks stay embedded in each role's Definition of Done.

### TASK-006: Finalize MVP scope doc, prohibited-wording policy, and Day 1 presentation story

- **Owner**: PM
- **Assignee**: PM / Planner
- **Branch**: `pm/TASK-006-day-1-allocation`
- **Status**: in_progress
- **Priority**: High
- **Day**: Day 1
- **Description**: Lock the P0/P1/P2 boundary for the hackathon, confirm prohibited wording against `standards.md` and `memory/glossary.md`, and draft the first presentation story.
- **Definition of Done**:
  - [ ] MVP scope is confirmed against PRD §6.3-6.5 with no P1/P2 pull-in.
  - [ ] Wording policy references `standards.md` and `memory/glossary.md`.
  - [ ] Draft key messages frame the product as information analysis and issue monitoring.
  - [ ] Any new wording avoids outcome prediction, causal assertion, and action-oriented framing.

### TASK-005: Wireframe dashboard/detail screens; start UI against dummy JSON

- **Owner**: Frontend Implementer
- **Assignee**: Frontend Implementer
- **Branch**: `frontend/TASK-005-dashboard-skeleton`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 1
- **Description**: Create the initial dashboard/detail screen structure and dummy-data contract so frontend work can proceed before the backend is complete.
- **Definition of Done**:
  - [ ] Home dashboard and issue detail skeletons exist.
  - [ ] Dummy JSON includes issue title, category, current reflected expectation value, 24h/7d changes, caution level, and data-as-of timestamp.
  - [ ] Every data-bearing placeholder has visible data-as-of and interpretation-caution placement.
  - [ ] UI copy passes the project wording policy.

### TASK-001: Repo scaffold

- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-001-repo-scaffold`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 1
- **Description**: Create the `/frontend` and `/backend` project shells using the agreed monorepo stack.
- **Definition of Done**:
  - [ ] `/frontend` exists with Vite, React, TypeScript, Tailwind CSS, and npm scripts.
  - [ ] `/backend` exists with FastAPI, Python package layout, and pip dependency files.
  - [ ] Local run commands are documented or discoverable in project files.
  - [ ] No secrets or environment files are printed or committed.

### TASK-011: Add `/api/health` endpoint

- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-011-health-endpoint`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 1
- **Description**: Add the minimal backend health endpoint early so local API setup can be verified quickly.
- **Definition of Done**:
  - [ ] `GET /api/health` returns a stable JSON status payload.
  - [ ] Endpoint uses FastAPI conventions and is included in OpenAPI docs.
  - [ ] Response does not expose secrets, credentials, or deployment internals.

### TASK-003: API contract draft and response-shape agreement

- **Owner**: Backend Implementer + PM
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-003-api-contract`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 1
- **Description**: Draft the read-only MVP API contract and align response fields with frontend dummy JSON and Data/AI sample output.
- **Definition of Done**:
  - [ ] Contract covers `/api/issues`, `/api/issues/:id`, `/api/issues/:id/history`, `/api/issues/:id/report`, and `/api/health`.
  - [ ] Responses include data-as-of timestamps and caution-level fields where metrics are present.
  - [ ] Public-facing route names use `issues`, `signals`, `reports`, and `categories`, not market-terminal vocabulary.
  - [ ] PM reviews names and response copy for safety framing before implementation depends on them.

### TASK-002: DB schema draft for MVP tables

- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-002-db-schema`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 1
- **Description**: Draft the MVP database schema for the batch-fed, read-only dashboard.
- **Definition of Done**:
  - [ ] Draft includes `markets`, `market_outcomes`, `market_snapshots`, `market_metrics`, `issue_signals`, `ai_reports`, `related_events`, and `data_collection_logs`.
  - [ ] No `users`, `watchlists`, wallet-level, or participant-level table is introduced.
  - [ ] Snapshot and metric tables follow the append-only strategy from Technical Design §4.10.
  - [ ] Human approval is obtained before applying schema changes to any shared or production database.

### TASK-004: Polymarket Gamma/CLOB live spike

- **Owner**: Data/AI Implementer
- **Assignee**: Data/AI Implementer
- **Branch**: `data-ai/TASK-004-polymarket-spike`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 1
- **Description**: Validate the public Polymarket data shape, identify usable fields for the MVP schema/API, and collect a small representative sample set.
- **Definition of Done**:
  - [ ] Gamma/CLOB field names, pagination, and practical rate-limit behavior are documented.
  - [ ] 10 active binary sample markets are captured with title, description, category/tag, current value, history token/source, volume/activity, liquidity, and timestamps where available.
  - [ ] Any missing or unstable fields are recorded in `memory/known-issues.md`.
  - [ ] Sample output is shared in a format the backend and frontend can consume for Day 2 work.

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
