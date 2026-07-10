<!--
Purpose:        Current project state snapshot — the first context file every agent reads
Owner:          All agents (read), PM / Backend Implementer (write)
Update Trigger: Day completed, milestone status shift, major decision made
Harness Version: 1.1
-->

# Project: Outlook Signals

_Last updated: 2026-07-10_

## Summary

Outlook Signals is an information-analysis dashboard that surfaces global issues whose reflected expectation value has recently shifted significantly in Polymarket's public prediction-market data. It helps users understand how an issue is being reassessed through change magnitude, time-series charts, and interpretation-caution notices — explicitly **not** a forecasting, betting, or trading tool.

Built as a **5-day hackathon MVP by a 4-person team**.

## Current State

- **Version**: v0.6.3-day5-v3-allocation
- **Phase**: Day 5 v3 implementation allocated
- **Next milestone**: Parallel v3 runtime implementation, integrated copy/contract review, final demo rehearsal, screenshot capture, and presentation polish
- **Overall health**: 🟢 Good — Day 4 core UI/API/event-candidate work, report-generation code readiness, broad Korean live category filtering, the 24h combined batch path, demo/deck draft, and final copy/wording lint are complete; OpenRouter-backed v2 summaries have been generated and verified for the default top-20 heat-sorted issues; ADR-033 freezes the approved eight-field v3 report contract; and `TASK-049`, `TASK-050`, `TASK-051`, and `TASK-053` now split the Day 5 implementation/review work

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
| Frontend | Dashboard v1 is integrated with backend routes and static fallback, including ranked issue cards, category/window/sort controls, detail view, Recharts line chart, error fallback states, data-as-of timestamps, caution badges, Day 3-hardened window-specific insufficient-history handling, shared footer copy, a dedicated in-app information notice surface, `TASK-043` report-card states/labels for the v2 issue-explainer summary, and `TASK-044` Korean issue display copy for raw English market titles. `TASK-051` is assigned to replace fixed v2 report rendering with ADR-033 dynamic sections shown as one visible card section at a time. |
| Backend | FastAPI app, `/api/health`, accepted `/api/issues`/detail/history/report/category contract, Pydantic schemas, and contract tests exist. `TASK-010` merged live issue list/detail/history read paths with documented static fallback behavior, `TASK-039` wires `/api/issues/{id}/report` to stored report rows in live mode while preserving the accepted empty state, `TASK-043` updates runtime report `content` to the v2 issue-explainer schema, and `ISS-007` makes the report endpoint serve current-prompt-version rows only. `TASK-048` and ADR-033 freeze the replacement eight-field v3 contract as documentation only; `TASK-050` is assigned to implement that schema/read contract. Runtime remains v2 until coordinated implementation closes. `/api/categories` now returns broad Korean filter labels derived from live servable issues, such as `정치`, `경제`, `기술`, `세계`, and `스포츠`; `/api/issues` category filtering accepts those Korean labels plus raw stored category values, while detailed issue-topic labels remain in the frontend card display layer. `001_initial_schema.sql` has been applied to the currently configured development Supabase DB after human approval; the DB has one live collector snapshot/metric row per normalized issue, ADR-025 adds a guarded historical seed path for richer live chart history, and PR #36 adds a guarded related-event seed path for four normalized/live-reachable demo issues. |
| Data/AI | `TASK-007` produced 50 normalized records and structured skip details; `TASK-008` computes 24h/7d metrics through a local/dev-safe path; `TASK-009` inserts MVP expectation-shift detector rows from the ±5pp threshold; `TASK-036` adds MVP caution thresholds and marker handoff guidance; `TASK-015` implements fixed-template report generation and safety filtering; `TASK-019` adds curated related-event candidates; `TASK-041` fixes report prompt-input lookup for historical-seed metric timestamps while preserving the no-fabrication skip path; `TASK-042` adds the combined data/metric/signal/report batch runner, dev-only reports-only command, and 24h scheduled workflow; `TASK-043` advances report generation to `PROMPT_VERSION=v2` with issue explainer and conditional scenario slots; `ISS-007` verified `success|v2|30` in the configured development DB and current v2 content for the default top-20 heat-sorted issues. `TASK-049` is assigned to implement ADR-033 v3 generation, validation, prompt-versioning, deterministic caution, and non-causal context handling. |
| PM / Safety | P0 scope remains locked; wording policy references `standards.md` and `memory/glossary.md`; `TASK-040` demo/deck draft is complete in `reports/task-040-demo-script-deck-draft.md`; `TASK-018` final copy/wording lint passed with notes in `reports/task-018-copy-lint.md`; Day 4 closeout evidence is recorded in `reports/day-4-closeout-plan.md`; `TASK-047` and ADR-032 preserve the original v3 scope-lock history, while user-approved TASK-048/ADR-033 now define the superseding eight-field contract and manual-only context boundary. `TASK-052` records the Day 5 allocation, and `TASK-053` is assigned as the final v3 integration copy/contract review. |

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
| 2026-07-09 | `TASK-042` completed: `app/core/scheduled_batch.py` links data collection, snapshot/metric generation, signal detection, and AI report generation in one command; `.github/workflows/daily-batch.yml` runs it every 24h; ADR-027 updates the provider path so the configured OpenRouter-style key is used through the OpenAI-compatible endpoint, and the current DB now has successful stored summaries for the top checked issues. |
| 2026-07-09 | `TASK-043` accepted and implemented: AI report output changed from numeric 5-section summaries to 8-section issue explainers with three neutral conditional scenario sections, and `/api/issues/{id}/report` now treats legacy v1 stored report content as `not_yet_generated` rather than serving a mismatched shape. |
| 2026-07-09 | `TASK-044` completed: dashboard/detail issue headings now use Korean topic labels, issue display names, and one-line 기준 조건 while preserving raw Polymarket titles only as detail-screen provenance. |
| 2026-07-09 | `ISS-007` resolved: report reads now require current `PROMPT_VERSION`, report regeneration treats same-timestamp current rows as fresh, `/api/categories` reflects live servable categories, category filtering is case-insensitive, and the configured development DB has v2 summaries for the default top-20 heat-sorted issues. |
| 2026-07-09 | Category filters were localized through ADR-031 and then simplified per user clarification: `/api/categories` now returns broad Korean groups such as `정치`, `경제`, `기술`, `세계`, and `스포츠`, while detailed labels such as `우크라이나 전쟁` and future `이란 전쟁` remain card-level display labels. |
| 2026-07-09 | `TASK-040` completed: Day 4 deck outline, demo script, fallback narration, Day 5 screenshot/rehearsal checklist, and judge Q&A draft are recorded in `reports/task-040-demo-script-deck-draft.md`; final cross-surface wording lint remains `TASK-018`. |
| 2026-07-09 | `TASK-018` completed: final Day 4 copy/wording lint passed with notes in `reports/task-018-copy-lint.md`; prompt-template wording, dashboard weekly-row data-as-of timing, and one TASK-044 report wording hit were resolved, with no policy/API/schema/dependency/infrastructure/deployment changes. |
| 2026-07-10 | Day 4 closed: latest `origin/main` includes PR #42 (`TASK-018`), no active Day 4 tasks remain, and `reports/day-4-closeout-plan.md` records the closeout evidence and Day 5 handoff. |
| 2026-07-10 | `TASK-047` completed: ADR-032 approved the v3 AI report policy, the exact v3 report field list, limited public API shape changes, tightened wording-safety criteria, manual-only context-candidate scope, and maintained prohibitions before implementation begins. |
| 2026-07-10 | `TASK-048` completed: ADR-033 supersedes ADR-032 for the v3 content/display contract, accepting the eight-field schema, Option A external context, exact caution matrix, evidence-first Frontend order, Unicode character bounds, and a maximum of five concise sentences per field without changing runtime v2 paths. |
| 2026-07-10 | `TASK-052` completed: latest `origin/main` at `106af52` was confirmed, Day 5 v3 implementation was split into `TASK-049` Data/AI generation, `TASK-050` Backend API/read contract, `TASK-051` Frontend dynamic report cards, and `TASK-053` final integration copy/contract review, with allocation evidence recorded in `reports/day-5-v3-implementation-allocation.md`. |

## Constraints

- 5-day build window, 4-person team — see `../ORCHESTRATOR.md` and `../roadmap.md` for day-by-day allocation
- No accounts/login/saving/notifications/reports/team-sharing in MVP (PRD §6.5)
- No free-form AI analysis, no automated news matching, no wallet-level participant features (see `AGENTS.md` Absolute Restrictions)
- V3 runtime work must follow ADR-033; runtime remains v2 until `TASK-049`,
  `TASK-050`, `TASK-051`, and `TASK-053` close.
- Every data-bearing screen requires a data-as-of timestamp + interpretation-caution badge (PRD §8.10)
- Strict prohibited-wording policy — see `glossary.md` and `../standards.md`
