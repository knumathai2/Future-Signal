<!--
Purpose:        Current project state snapshot — the first context file every agent reads
Owner:          All agents (read), PM / Backend Implementer (write)
Update Trigger: Day completed, milestone status shift, major decision made
Harness Version: 1.1
-->

# Project: Outlook Signals

_Last updated: 2026-07-08_

## Summary

Outlook Signals is an information-analysis dashboard that surfaces global issues whose reflected expectation value has recently shifted significantly in Polymarket's public prediction-market data. It helps users understand how an issue is being reassessed through change magnitude, time-series charts, and interpretation-caution notices — explicitly **not** a forecasting, betting, or trading tool.

Built as a **5-day hackathon MVP by a 4-person team**.

## Current State

- **Version**: v0.2.0-day2-allocation
- **Phase**: Day 2 assigned; data pipeline and core API/UI integration ready to start
- **Next milestone**: Day 2 — real data path through ranking API and dashboard v1 (see `../roadmap.md` and `../reports/day-2-work-allocation.md`)
- **Overall health**: 🟢 Good — the project now has a working local skeleton and remains within the narrowed MVP scope

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
| Frontend | Dashboard, issue cards, detail view, Recharts line chart, caution badges, data-as-of timestamps, fallback states, and template-summary shell run against typed dummy data. Day 2 `TASK-012` is assigned to reconcile the dummy shape with `/api/issues` and render ranked API-or-fallback data. |
| Backend | FastAPI app, `/api/health`, accepted `/api/issues`/detail/history/report/category contract, Pydantic schemas, and contract tests exist. `TASK-010` PR #10 now wires issue list/detail/history to live reads with static fallback and is in review. Schema draft is accepted but unapplied. |
| Data/AI | Gamma/CLOB field shape, pagination, rate-limit behavior, CLOB history query shape, and a 10-item sample set are documented. Day 2 `TASK-007`, `TASK-008`, and `TASK-009` are assigned for normalization, metrics, and the MVP expectation-shift detector. |
| PM / Safety | P0 scope remains locked; wording policy references `standards.md` and `memory/glossary.md`; Day 2 allocation is recorded in `reports/day-2-work-allocation.md`, and PM now acts as scope gatekeeper while implementation proceeds. |

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
| 2026-07-08 | PR #10 (`TASK-010`) reviewed; reviewer hardening added for live detail/history fallback paths and ADR-013 confirmation remains required before merge |

## Constraints

- 5-day build window, 4-person team — see `../ORCHESTRATOR.md` and `../roadmap.md` for day-by-day allocation
- No accounts/login/saving/notifications/reports/team-sharing in MVP (PRD §6.5)
- No free-form AI analysis, no automated news matching, no wallet-level participant features (see `AGENTS.md` Absolute Restrictions)
- Every data-bearing screen requires a data-as-of timestamp + interpretation-caution badge (PRD §8.10)
- Strict prohibited-wording policy — see `glossary.md` and `../standards.md`
