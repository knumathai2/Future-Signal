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
| TASK-003 | API contract draft and response-shape agreement | Backend Implementer + PM | Backend Implementer | `backend/TASK-003-api-contract` | review |
| TASK-002 | DB schema draft for MVP tables | Backend Implementer | Backend Implementer | `backend/TASK-002-db-schema` | review |
| TASK-004 | Polymarket Gamma/CLOB live spike; confirm field structure and collect 10 sample markets | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-004-polymarket-spike` | assigned |

`TASK-001`, `TASK-005`, and `TASK-011` completed 2026-07-08 — see `tasks/completed.md`.

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

### TASK-003: API contract draft and response-shape agreement

- **Owner**: Backend Implementer + PM
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-003-api-contract`
- **Status**: review (blocked on PM sign-off)
- **Priority**: High
- **Day**: Day 1
- **Description**: Draft the read-only MVP API contract and align response fields with frontend dummy JSON and Data/AI sample output.
- **Definition of Done**:
  - [x] Contract covers `/api/issues`, `/api/issues/:id`, `/api/issues/:id/history`, `/api/issues/:id/report`, and `/api/health`. Also includes `/api/categories`.
  - [x] Responses include data-as-of timestamps and caution-level fields where metrics are present.
  - [x] Public-facing route names use `issues`, `signals`, `reports`, and `categories`, not market-terminal vocabulary (test-enforced: `backend/tests/test_issues_contract.py`).
  - [ ] PM reviews names and response copy for safety framing before implementation depends on them.
- **Notes**: Draft is runnable — Pydantic schemas + mock-data routes in `backend/app/schemas/issues.py` / `backend/app/api/routes/issues.py`, full writeup in `backend/API_CONTRACT.md`. One open item flagged for PM: Technical Design §5's "`204` with a body hint" for not-yet-generated reports is invalid per HTTP semantics (204 cannot carry a body); drafted as `200` + `{"status": "not_yet_generated"}` instead, pending confirmation.

### TASK-002: DB schema draft for MVP tables

- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-002-db-schema`
- **Status**: review (draft complete, not applied)
- **Priority**: High
- **Day**: Day 1
- **Description**: Draft the MVP database schema for the batch-fed, read-only dashboard.
- **Definition of Done**:
  - [x] Draft includes `markets`, `market_outcomes`, `market_snapshots`, `market_metrics`, `issue_signals`, `ai_reports`, `related_events`, and `data_collection_logs`.
  - [x] No `users`, `watchlists`, wallet-level, or participant-level table is introduced.
  - [x] Snapshot and metric tables follow the append-only strategy from Technical Design §4.10.
  - [ ] Human approval is obtained before applying schema changes to any shared or production database — **not yet requested; schema remains unapplied.**
- **Notes**: Draft DDL at `backend/migrations/001_initial_schema.sql`, mirrored as SQLAlchemy models in `backend/app/db/models.py` (not wired to any route). Plain SQL used instead of Alembic since the migration-tool choice is still an open Day 1 decision (`commands.md`).

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
