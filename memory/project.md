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

- **Version**: v0.1.0-day1
- **Phase**: Day 1 kickoff implementation complete; review/approval gates remain for DB schema and API contract
- **Next milestone**: Day 2 — data pipeline + core UI/API integration (see `../roadmap.md`)
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
| Frontend | Dashboard, issue cards, detail view, Recharts line chart, caution badges, data-as-of timestamps, fallback states, and template-summary shell run against typed dummy data. |
| Backend | FastAPI app, `/api/health`, draft `/api/issues`/detail/history/report/category routes, Pydantic schemas, and contract tests exist. Routes return hardcoded sample data until DB wiring starts. |
| Data/AI | Gamma/CLOB field shape, pagination, rate-limit behavior, CLOB history query shape, and a 10-item sample set are documented. Batch collector and metric persistence are Day 2 work. |
| PM / Safety | P0 scope remains locked; wording policy references `standards.md` and `memory/glossary.md`; Day 1 status checkpoint is recorded in `reports/day-1-implementation-status.md`. |

## Recent Changes

| Date | Change |
|------|--------|
| 2026-07-07 | AI Development Harness v1.1 initial setup (Standard tier) |
| 2026-07-07 | PRD rescoped to v1.1 (hackathon-narrowed from broader "global issue outlook platform" concept) |
| 2026-07-07 | Service Design, Technical Design, UX Design written as companion specs to PRD |
| 2026-07-08 | Day 1 implementation scaffold completed: frontend dummy flow, backend mock API contract, DB schema draft, health endpoint |
| 2026-07-08 | Polymarket Gamma/CLOB spike completed with 10 sample records and a CLOB history fixture |
| 2026-07-08 | Day 1 implementation status checkpoint recorded in `reports/day-1-implementation-status.md` |

## Constraints

- 5-day build window, 4-person team — see `../ORCHESTRATOR.md` and `../roadmap.md` for day-by-day allocation
- No accounts/login/saving/notifications/reports/team-sharing in MVP (PRD §6.5)
- No free-form AI analysis, no automated news matching, no wallet-level participant features (see `AGENTS.md` Absolute Restrictions)
- Every data-bearing screen requires a data-as-of timestamp + interpretation-caution badge (PRD §8.10)
- Strict prohibited-wording policy — see `glossary.md` and `../standards.md`
