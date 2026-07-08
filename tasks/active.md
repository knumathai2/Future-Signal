<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-08_

## In Progress

Day 2 work is assigned as of 2026-07-08. The goal is to connect the real data path through the core dashboard flow while keeping P1/P2 items deferred.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-007 | Batch collector: fetch + normalize (steps 1-2) | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-007-fetch-normalize` | review |
| TASK-008 | Batch collector: snapshot + metrics (steps 3-5) | Data/AI Implementer + Backend | Data/AI Implementer + Backend Implementer | `data-ai/TASK-008-snapshot-metrics` | assigned |
| TASK-009 | Expectation-shift detection (±5pp threshold) | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-009-shift-detection` | assigned |
| TASK-010 | `/api/issues`, `/api/issues/:id`, `/api/issues/:id/history` | Backend Implementer | Backend Implementer | `backend/TASK-010-core-api` | review |

`TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005`, `TASK-006`, `TASK-011`, `TASK-012`, and `TASK-031` completed 2026-07-08 — see `tasks/completed.md`.

## Day 2 Assignment Notes

- **PM / Planner** completed the Day 2 allocation and Q&A seed in `TASK-031`. PM now acts as scope gatekeeper while implementation proceeds. Do not promote P1/P2 features while the data/API/dashboard path is incomplete.
- **Data/AI Implementer** starts with `TASK-007`; `TASK-008` starts only after normalized objects are validated against the accepted schema draft. Shared or production DB schema application still requires separate human approval under `AGENTS.md`.
- **Backend Implementer** starts `TASK-010` by preserving the accepted public API shape, updating stale contract wording if needed, and preparing the read path for latest metrics/history once `TASK-008` produces data.
- **Frontend Implementer** starts `TASK-012` with dummy/API shape reconciliation, then replaces dummy ranking data only after the backend endpoint is stable enough for local integration.
- **Reviewer / Debugger** stay embedded unless a concrete blocker appears. Any user-facing copy changed during Day 2 must pass the project wording lint before review.

## Day 2 Handoff Order

1. `TASK-007` produces normalized 30-50 market records or a named blocker.
2. `TASK-008` persists snapshots/metrics in the approved draft shape, or uses a local/dev-only fallback until a shared DB is approved.
3. `TASK-010` serves the accepted issue list/detail/history contract from the latest available data, with honest `data_as_of` timestamps.
4. `TASK-012` renders ranked issue cards from the API response and keeps the static dummy-data fallback available.
5. `TASK-009` adds the MVP threshold detector after `change_24h` is available; the UI can surface it through the existing caution/marker pattern later.

## Day 2 Active Task Details

### TASK-007: Batch collector fetch + normalize
- **Owner**: Data/AI Implementer
- **Assignee**: Data/AI Implementer
- **Branch**: `data-ai/TASK-007-fetch-normalize`
- **Status**: review
- **Priority**: High
- **Day**: Day 2
- **Description**: Implement Gamma/CLOB fetch and normalization for the curated 30-50 binary-market sample set using the Day 1 spike findings.
- **Definition of Done**:
  - [x] Curated market input list is documented or generated from accepted sample criteria.
  - [x] Normalized records include required market/outcome/current-value/activity fields.
  - [x] Invalid records are skipped with structured error details instead of failing the whole run.
  - [x] A local run produces a normalized sample artifact suitable for `TASK-008` and `TASK-010`.

### TASK-008: Batch collector snapshot + metrics
- **Owner**: Data/AI Implementer + Backend
- **Assignee**: Data/AI Implementer + Backend Implementer
- **Branch**: `data-ai/TASK-008-snapshot-metrics`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 2
- **Description**: Store current snapshots and calculate `change_24h`, `change_7d`, `heat_score`, and `confidence_level` from the accepted schema draft.
- **Definition of Done**:
  - [ ] Snapshot and metric rows can be produced from normalized data in a local/dev-safe path.
  - [ ] Missing 24h/7d references produce `null` metrics plus `insufficient_data`, never fabricated values.
  - [ ] `data_as_of` and calculation reference time are available for API payloads.
  - [ ] Shared or production database writes are not performed without explicit human approval.

### TASK-009: Expectation-shift detection
- **Owner**: Data/AI Implementer
- **Assignee**: Data/AI Implementer
- **Branch**: `data-ai/TASK-009-shift-detection`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 2
- **Description**: Add the MVP threshold detector for `abs(change_24h) >= 5pp` with duplicate suppression for the same window.
- **Definition of Done**:
  - [ ] Threshold is implemented as a named constant with tests around boundary values.
  - [ ] Detector emits only the MVP `expectation_shift` type and `medium` severity.
  - [ ] Duplicate detections in the same rolling window are suppressed.
  - [ ] Output is ready for the detail/API response shape without adding P1 feed scope.

### TASK-010: Core read API endpoints
- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-010-core-api`
- **Status**: review
- **Priority**: High
- **Day**: Day 2
- **Description**: Replace hardcoded issue responses with a read path aligned to the accepted contract and latest available metrics/history.
- **Definition of Done**:
  - [x] `/api/issues`, `/api/issues/{id}`, and `/api/issues/{id}/history` preserve the accepted response fields.
  - [x] Query params remain Pydantic-validated for `window`, `sort`, `limit`, and `offset`.
  - [x] Unknown IDs and invalid params have tested error behavior.
  - [x] Last-known-good or static fallback behavior is documented if live data is unavailable.
  - [x] No public path or schema field introduces prohibited market-terminal wording.

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
