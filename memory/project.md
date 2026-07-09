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

- **Version**: v0.6.0-day4-assigned
- **Phase**: Day 4 active
- **Next milestone**: Day 4 closeout — demo/deck draft and final wording-safety pass
- **Overall health**: 🟡 Watch — Day 4 core UI/API/event-candidate work, report-generation code readiness, and the 24h combined batch path are complete; stored live/dev summaries are still absent because the current OpenAI key returns authentication failures

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
    ├── backend/                # FastAPI scaffold, read API, schema/migration
    ├── reports/                # Implementation status and data-spike findings
    └── memory/                 # Working project/session state
```

## Implementation Snapshot

| Area | Current state |
|---|---|
| Frontend | Dashboard v1 is integrated with backend routes and static fallback, including ranked issue cards, category/window/sort controls, detail view, Recharts line chart, error fallback states, data-as-of timestamps, caution badges, Day 3-hardened window-specific insufficient-history handling, shared footer copy, a dedicated in-app information notice surface, and `TASK-016` report-card states for success/loading/not-yet-generated/fetch-failure. |
| Backend | FastAPI app, `/api/health`, accepted `/api/issues`/detail/history/report/category contract, Pydantic schemas, and contract tests exist. `TASK-010` merged live issue list/detail/history read paths with documented static fallback behavior, and `TASK-039` wires `/api/issues/{id}/report` to latest successful stored report rows in live mode while preserving the accepted empty state. `001_initial_schema.sql` has been applied to the currently configured development Supabase DB after human approval; the DB has one live collector snapshot/metric row per normalized issue, ADR-025 adds a guarded historical seed path for richer live chart history, and PR #36 adds a guarded related-event seed path for four normalized/live-reachable demo issues. |
| Data/AI | `TASK-007` produced 50 normalized records and structured skip details; `TASK-008` computes 24h/7d metrics through a local/dev-safe path; `TASK-009` inserts MVP expectation-shift detector rows from the ±5pp threshold; `TASK-036` adds MVP caution thresholds and marker handoff guidance; `TASK-015` implements fixed-template report generation and safety filtering; `TASK-019` adds curated related-event candidates; `TASK-041` fixes report prompt-input lookup for historical-seed metric timestamps while preserving the no-fabrication skip path; `TASK-042` adds the combined data/metric/signal/report batch runner, dev-only reports-only command, and 24h scheduled workflow. |
| PM / Safety | P0 scope remains locked; wording policy references `standards.md` and `memory/glossary.md`; remaining Day 4 active work is sequenced in `reports/day-4-work-allocation.md` with `TASK-040` and final copy lint `TASK-018` assigned. |

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
| 2026-07-09 | `TASK-036` completed: caution-level thresholds and expectation-shift marker handoff documented in ADR-019. |
| 2026-07-09 | `TASK-014` completed: caution badge placement and copy aligned across dashboard/detail surfaces. |
| 2026-07-09 | `TASK-017` completed: brief caution copy, shared footer copy, and a dedicated in-app information notice surface were added without policy, route dependency, API, schema, or infrastructure changes. |
| 2026-07-09 | Day 3 closed: all Day 3 P0 tasks are merged and closeout evidence is recorded in `reports/day-3-closeout-plan.md`. |
| 2026-07-09 | Day 4 work assigned from latest `origin/main` at `af83f7e`: `TASK-015`, `TASK-039`, `TASK-016`, `TASK-019`, `TASK-040`, and `TASK-018` are active; `TASK-038` records allocation and guardrails in `reports/day-4-work-allocation.md`. |
| 2026-07-09 | `TASK-015` completed: fixed-template AI report generator, strict schema parse, and banned-phrase/pattern safety filter implemented (`app/core/ai_report.py`, `app/core/ai_report_batch.py`, 38 new tests). ADR-022 records the human-approved AI provider decision (OpenAI, real `OpenAIReportClient`) overriding Day 4's deterministic-template default - no key configured in this environment, so no live call has executed yet. |
| 2026-07-09 | `TASK-039` completed in PR #29 follow-up: report endpoint live read-path now serves latest successful `ai_reports` rows, keeps `not_yet_generated` for absent/failed reads, and history fallback returns empty points rather than fabricated chart data. |
| 2026-07-09 | `TASK-016` completed: the frontend detail flow consumes `/api/issues/{id}/report` and renders stored report sections plus loading, not-yet-generated, and fetch-failure states with nearby data-as-of timing and caution context. |
| 2026-07-09 | Development Supabase connectivity was restored through the pooler URL, `psycopg2-binary==2.9.10` was added for provider-copied `postgresql://...` URLs, and `backend/migrations/001_initial_schema.sql` was applied after explicit human approval. |
| 2026-07-09 | `ISS-004` seeded the configured development DB with one collector snapshot/metric row per normalized issue, and ADR-025 added the approved local/dev historical seed path for live DB-backed demo charts. |
| 2026-07-09 | The guarded historical seed path was run against the configured development DB: 33,238 total snapshot rows, 150 metric rows, 2 expectation-shift signal rows, and 7d live chart/metric coverage for the 50 seeded issues. |
| 2026-07-09 | `TASK-019` completed and merged in PR #36 at `6d0eb44`: related-event candidates are curated for exactly four normalized/live-reachable issue IDs with a guarded local/dev seed script and tests. |
| 2026-07-09 | `TASK-041` created: AI report generation readiness must close the remaining live/dev gap where `ai_reports=0` and latest historical-seed metric timestamps do not exactly match snapshot timestamps required by the current prompt-input lookup. |
| 2026-07-09 | `TASK-041` completed from `origin/main` at `01df91b`: report prompt inputs now use the latest snapshot at or before the metric timestamp, tests prove fake-LLM success-row insertion, and approved-only run notes document how to create stored summaries later. |
| 2026-07-09 | `TASK-042` completed: `app/core/scheduled_batch.py` links data collection, snapshot/metric generation, signal detection, and AI report generation in one command; `.github/workflows/daily-batch.yml` runs it every 24h; the dev `--reports-only` command was attempted against the configured DB but OpenAI returned `401 Unauthorized`, leaving `ai_reports_success=0`. |

## Constraints

- 5-day build window, 4-person team — see `../ORCHESTRATOR.md` and `../roadmap.md` for day-by-day allocation
- No accounts/login/saving/notifications/reports/team-sharing in MVP (PRD §6.5)
- No free-form AI analysis, no automated news matching, no wallet-level participant features (see `AGENTS.md` Absolute Restrictions)
- Every data-bearing screen requires a data-as-of timestamp + interpretation-caution badge (PRD §8.10)
- Strict prohibited-wording policy — see `glossary.md` and `../standards.md`
