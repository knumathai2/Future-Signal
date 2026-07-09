<!--
Purpose:        Current project state snapshot — the first context file every agent reads
Owner:          All agents (read), PM / Backend Implementer (write)
Update Trigger: Day completed, milestone status shift, major decision made
Harness Version: 1.1
-->

# Project: Outlook Signals

_Last updated: 2026-07-09_

## Summary

Outlook Signals is an information-analysis dashboard that surfaces global issues whose reflected expectation value has recently shifted significantly in Polymarket's public prediction-market data. It helps users understand how an issue is being reassessed through change magnitude, time-series charts, and interpretation-caution notices — explicitly **not** a forecasting, betting, or trading tool.

Built as a **5-day hackathon MVP by a 4-person team**.

## Current State

- **Version**: v0.4.0-day3-open
- **Phase**: Day 3 in progress; detail/chart path hardened
- **Next milestone**: Day 3 closeout — issue detail screen, chart/tooltip refinement, inflection-point markers, and interpretation-caution badge logic
- **Overall health**: 🟢 Good — the Day 2 data/API/dashboard path is merged, verified, and Day 3 active work is scoped to the narrowed MVP path

## Tech Summary

| Field | Value |
|-------|-------|
| Language | TypeScript (frontend) + Python (backend/data/AI) |
| Framework | React + Vite + Tailwind + Recharts (frontend) / FastAPI (backend) |
| Infrastructure | Vercel + Railway/Render + Supabase/Neon |
| Repo Structure | Single monorepo (`/frontend`, `/backend`) |

## Key Paths

```
Future Signal/
└── AI Development Harness/     # Working root
    ├── docs/
    │   ├── prd/                # Product requirements (v1.1, split by section)
    │   ├── service-design/     # Data/metrics/AI/signal spec (v1.0)
    │   ├── tech-design/        # Architecture/schema/API/pipeline spec (v1.0)
    │   └── ux-design/          # Screens/copy policy/safety guardrails (v1.0)
    ├── frontend/               # React/Vite dummy-data dashboard/detail/chart flow
    ├── backend/                # FastAPI scaffold, mock read API, schema draft
    ├── reports/                # Implementation status and data-spike findings
    └── memory/                 # Working project/session state
```

## Implementation Snapshot

| Area | Current state |
|---|---|
| Frontend | Dashboard v1 is integrated with backend routes and static fallback, including ranked issue cards, category/window/sort controls, detail view, Recharts line chart, error fallback states, data-as-of timestamps, caution badges, and Day 3-hardened window-specific insufficient-history handling. |
| Backend | FastAPI app, `/api/health`, accepted `/api/issues`/detail/history/report/category contract, Pydantic schemas, and contract tests exist. `TASK-010` merged live issue list/detail/history read paths with documented static fallback behavior. Schema draft is accepted but unapplied. |
| Data/AI | `TASK-007` produced 50 normalized records and structured skip details; `TASK-008` computes 24h/7d metrics through a local/dev-safe path; `TASK-009` inserts MVP expectation-shift detector rows from the ±5pp threshold. |
| PM / Safety | P0 scope remains locked; wording policy references `standards.md` and `memory/glossary.md`; Day 3 work is assigned in `tasks/active.md` and sequenced in `reports/day-3-work-allocation.md`. |

## Recent Changes

| Date | Change |
|------|--------|
| 2026-07-07 | AI Development Harness v1.1 initial setup (Standard tier) |
| 2026-07-07 | PRD rescoped to v1.1 (hackathon-narrowed from broader "global issue outlook platform" concept) |
| 2026-07-07 | Service Design, Technical Design, UX Design written as companion specs to PRD |
| 2026-07-08 | Day 1 implementation scaffold completed: frontend dummy flow, backend mock API contract, DB schema draft, health endpoint |
| 2026-07-08 | Polymarket Gamma/CLOB spike completed with 10 sample records and a CLOB history fixture |
| 2026-07-08 | Day 1 implementation status checkpoint recorded in `reports/day-1-implementation-status.md` |
| 2026-07-08 | Day 1 closed: API contract accepted (ADR-008), DB schema draft accepted but unapplied (ADR-011), no Day 1 tasks remain active |
| 2026-07-08 | Day 2 work assigned: `TASK-031` completed the allocation; `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`, and `TASK-012` moved into active execution order |
| 2026-07-08 | PR #9 (`TASK-007`) merged 50 normalized sample records and structured skip details |
| 2026-07-08 | PR #10 (`TASK-010`) added live core API read paths with static fallback behavior |
| 2026-07-08 | PR #12 (`TASK-012`) reviewed; nullable change metrics now remain visible as insufficient data instead of `0.0pp` |
| 2026-07-08 | PR #13 (`TASK-008`) merged 24h/7d snapshot metric calculation |
| 2026-07-08 | PR #14 (`TASK-009`) merged the MVP expectation-shift detector |
| 2026-07-08 | PR #15 recorded local stack startup verification notes |
| 2026-07-08 | Day 2 closed; `tasks/active.md` has no remaining Day 2 tasks and Day 3 is ready to start |
| 2026-07-09 | Day 3 work assigned: `TASK-013`, `TASK-014`, `TASK-017`, `TASK-035`, and `TASK-036` opened in `tasks/active.md`; `TASK-034` records the PM allocation in `reports/day-3-work-allocation.md` |
| 2026-07-09 | `TASK-035` closed: detail/history API contract confirmed sufficient for the Day 3 chart/marker path with no response-shape change; live-read/fallback/unknown-id/history-window test coverage strengthened (62 backend tests passing) |
| 2026-07-09 | `TASK-013` completed: detail chart windows now require baseline-covered history, 30d no longer falls back to 7d, tooltips include timestamp/value/previous-point pp change, and chart markers consume API `signals` when present while preserving local 5pp fallback detection. |

## Constraints

- 5-day build window, 4-person team — see `../ORCHESTRATOR.md` and `../roadmap.md` for day-by-day allocation
- No accounts/login/saving/notifications/reports/team-sharing in MVP (PRD §6.5)
- No free-form AI analysis, no automated news matching, no wallet-level participant features (see `AGENTS.md` Absolute Restrictions)
- Every data-bearing screen requires a data-as-of timestamp + interpretation-caution badge (PRD §8.10)
- Strict prohibited-wording policy — see `glossary.md` and `../standards.md`
