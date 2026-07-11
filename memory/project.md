<!--
Purpose:        Current project state snapshot — the first context file every agent reads
Owner:          All agents (read), PM / Backend Implementer (write)
Update Trigger: Day completed, milestone status shift, major decision made
Harness Version: 1.1
-->

# Project: Outlook Signals

_Last updated: 2026-07-11_

## Summary

Outlook Signals is an information-analysis dashboard that surfaces global issues whose reflected expectation value has recently shifted significantly in Polymarket's public prediction-market data. It helps users understand how an issue is being reassessed through change magnitude, time-series charts, and interpretation-caution notices — explicitly **not** a forecasting, betting, or trading tool.

Built as a **5-day hackathon MVP by a 4-person team**.

## Current State

- **Version**: v0.13.0-v6-baseline-v7-planning
- **Phase**: V6 baseline preserved; on-demand v7 program awaiting implementation approvals
- **Next milestone**: Implement TASK-104 on-demand generation service and scheduled-workflow separation
- **Overall health**: 🟢 TASK-099~103 are complete. V7 writer, request/event schema, and broad A-D context policy pass focused tests; v6 remains public until TASK-105.

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
| Frontend | TASK-063 replaces the v3 step navigator with a strict v4 change-episode card. It validates the full evidence bundle, conditionally renders zero to three candidate/source cards, links exact candidate IDs to chart markers, keeps secure external links/timing/caution, and passes 320px/375px/desktop QA. Existing routed Home/list/detail/methodology information architecture remains intact. |
| Backend | TASK-062 activates the strict v4 report read contract and returns only reconstructed, evidence-consistent bundles with verified same-episode candidates and approved source fields. Legacy/failed/malformed/mismatched rows remain audit-only. TASK-057's append-only migration was applied to the approved development DB during TASK-065; production remains untouched. |
| Data/AI | TASK-058/059 provide bounded annotation-only research and deterministic/independent verification. TASK-060 connects them between signals and reports, and TASK-061 adds strict evidence-linked v4 generation with deterministic metric/context fields, same-episode verified candidates, writer-cost accounting, and last-known-good failure isolation. |
| PM / Safety | The v3 MVP remains frozen. ADR-038 activates TASK-056~065 with verified-only automated context, strict evidence links, a cumulative USD 100 OpenRouter cap, and local/development-only writes. Deployment and production DB writes remain separate gates. |
| v4 program | TASK-056~065 are complete. Migration 002 exists only in the approved development DB. ADR-047 permits bounded provider query reformulation with normalized market-metadata overlap while every evidence/publication gate remains unchanged. Fifty backfill targets yielded 46 completed distinct issues, seven rejected candidates, zero public candidates, and 14 successful v4 rows across 13 issues. |
| v5 program | ADR-048 expands the two authored v4 fields into six evidence-bounded narrative fields, adds explicit verified-source/no-source presentation, and activates sequential TASK-075~081 for implementation, development regeneration, and user quality review. |
| grounding program | ADR-049/TASK-082~091 add unapplied migration 003, source resolution evidence, writer/research grounding, one-to-four completeness-scaled scenarios, exact-title/reference/history validation, strict basis fields, and issue-type adversarial gates. Full Backend/Frontend checks pass; no external call, deployment, or non-test DB write occurred. |

## Recent Changes

| Date | Change |
|------|--------|
| 2026-07-11 | TASK-103 added the tested v7 30-day context path, A-D source levels, excerpt-backed claims, and conditional independent verification without a live provider call. |
| 2026-07-11 | TASK-102 added unapplied migration 004 and tested immutable request plus append-only lease/outcome event models. Earlier migrations remain untouched. |
| 2026-07-11 | TASK-101 activated the approved positive-first v7 writer/source policy and added strict flexible writer models, opaque evidence refs, parser, validation, and tests. No provider, database, schema, API, or workflow action occurred. |
| 2026-07-11 | TASK-100 archived the v1-v6 contract map, separated permanent evidence/safety invariants from version-specific shape/style rules, and recorded the retention and separately approved cleanup boundary. No runtime or external state changed. |
| 2026-07-11 | TASK-099 defined the proposed positive-first, user-requested, cache-backed v7 briefing direction and TASK-100~109 execution sequence. Implementation gates remain pending. |
| 2026-07-11 | TASK-095 activated the v6-only report endpoint with strict DB evidence reconstruction, four mode unions, exact sources/rule reference, v5 exclusion, and previous-valid-v6 fallback. Full Backend verification passed with 383 tests. |
| 2026-07-11 | TASK-094 resolved ISS-014: incomplete requested context configuration now records a safe failure reason, failed batch/log state, and CLI exit code one; explicit skip remains normal. No workflow configuration changed. |
| 2026-07-11 | TASK-093 completed the deterministic four-mode v6 writer/storage contract, metric/rule single-owner enforcement, evidence-basis separation, duplicate/rule-leak/current-fact gates, and append-only batch path. Full Backend verification passed with 369 tests. |
| 2026-07-11 | TASK-092 proposed ADR-050 and the four deterministic v6 briefing modes, strict evidence bases, single-owner non-duplication rules, collapsed resolution reference, and exact public response shape. TASK-093~098 are dependency-ordered; implementation awaits explicit AI-policy/API approval. |
| 2026-07-11 | After explicit user approval, append-only migration 003 was applied to the configured `ENV=local` development Supabase database. Table, columns, index, and unique constraint verification passed; `market_resolution_rules` contains zero rows. No provider call or report regeneration occurred. |
| 2026-07-11 | TASK-081 complete: actual v4/v5 comparison, display-value refinement, ten-report quality regeneration with six successes/four safe rejections, USD 0.376609 total observed v5 writer spend, documented limitations, and open local review screen. TASK-075~081 program complete. |
| 2026-07-11 | TASK-080 complete: 14 valid v5 rows across 13 development issues, 13/13 strict reconstruction, actual no-source Browser flow, fixture 0/1/3 evidence, responsive/loading/error/link/console QA, USD 0.268466 observed writer spend, 333 Backend tests, and all Frontend checks. TASK-081 activated. |
| 2026-07-11 | TASK-079 complete: v5 AI briefing UI, scenario/check/watch cards, visible no-source state, safe exact source links, strict parser, full Frontend checks, and responsive Browser QA. TASK-080 activated. |
| 2026-07-11 | TASK-078 complete: no-migration v5 JSONB storage/read contract, newest-to-oldest last-good reconstruction, exact verified-source API, OpenAPI update, and 332 Backend tests. TASK-079 activated. |
| 2026-07-11 | TASK-077 complete: user-format v5 contract, 3–4 conditional scenarios, typed check/watch lists, issue-specific/numeric gates, title/entity/official-domain queries, market/forecast-page exclusion, seven guarded development research rows, USD 0.18057005 task spend, and 331 Backend tests. TASK-078 activated. |
| 2026-07-11 | TASK-076 complete: strict six-field v5 narrative generation, specificity/duplication/evidence/wording gates, append-only batch storage, and 327 Backend tests. TASK-077 activated. |
| 2026-07-11 | TASK-075 complete: ADR-048 records human approval for the evidence-bounded v5 narrative and exact verified-source-link program; TASK-076 is activated. |
| 2026-07-11 | TASK-065 complete: 50-target development backfill, 46 distinct completed issues, query/result maxima 5/26, zero public candidates after strict gates, 13 successful v4 issue reports with zero safety/evidence mismatch, five live no-candidate and five local fixture candidate Browser flows, and USD 3.00263875 recorded spend. |
| 2026-07-11 | ADR-047 human-approved: bounded query reformulation may replace exact-string membership when normalized market topic/entity overlap passes; all annotation, independent-verification, and publication gates remain unchanged. TASK-065 resumed. |
| 2026-07-11 | Historical TASK-065 checkpoint: development migration applied; 16 bounded preflight runs across five issues recorded USD 0.778926. Bulk backfill paused until the later ADR-047 approval recorded above. |
| 2026-07-11 | TASK-064 approved after fixing UTC normalization in the SQLite local writer path; full integration/adversarial review reached 311 Backend tests and all Frontend/Browser checks. |
| 2026-07-11 | TASK-063 completed: strict v4 parser, one-card change episode, candidate/source cards, chart-ID linkage, responsive and state Browser QA. |
| 2026-07-11 | TASK-062 completed: strict v4 read-time reconstruction, verified-only candidate/source output, legacy/malformed gating, OpenAPI contract, and 309-test Backend verification. |
| 2026-07-11 | TASK-061 completed: strict seven-field evidence-grounded v4 generation, same-episode metric/candidate references, writer budget accounting, and failure-preserving storage passed the 298-test Backend suite. |
| 2026-07-11 | ADR-038 accepted and TASK-056~065 activated; TASK-056 policy/contract documentation completed without provider calls or DB writes. |
| 2026-07-11 | TASK-096 completed the strict four-mode v6 Frontend, collapsed resolution reference, safe exact source links, and 20-combination responsive Browser QA; TASK-097 development regeneration is active. |
| 2026-07-11 | TASK-097 evaluated the user-limited ten-issue development subset for USD 0.051373. Strict filtering preserved safety but yielded zero successful v6 rows; exact issue-anchor and scenario/material prompt corrections pass locally, while a small provider revalidation remains pending as ISS-015. |
| 2026-07-11 | TASK-097 completed after the user-approved two-issue retry: actual Trump stable/no-evidence and Israeli-parliament change/no-evidence v6 rows stored and served successfully for USD 0.007316 retry cost (USD 0.058689 total TASK-097 writer cost). ISS-015 is resolved and TASK-098 review is active. |
| 2026-07-11 | TASK-098 completed the v6 integration review: 388 Backend tests and all Frontend checks pass; four modes pass the 20-case Browser matrix; actual Trump and Israeli v6 flows pass stored/API/UI audits; the actual Trump screen is left open with recorded zero-candidate, prose-polish, pool, and runtime-verifier limits. |
| 2026-07-11 | TASK-098 reopened after detecting authored `december` repetition and generic English in the two live rows. New date/language read gates pass 390 Backend tests and fail closed both rows; TASK-097 is active pending approval for one clean Trump regeneration. |
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
| 2026-07-10 | `TASK-053` completed on the Reviewer integration branch: TASK-049/050/051 were combined, ADR-033 sentence/semantic/copy gaps were closed, 198 Backend tests and all Frontend checks passed, and 320px/375px null/non-null context Browser QA passed. |
| 2026-07-10 | `ISS-010` resolved the daily GitHub Actions failure: repository secrets/model configuration were restored without exposing values, the v3 prompt was aligned with existing ADR-033 constraints, and run `29073226485` passed with 50 processed, 0 failed, and 10 successful reports. Draft PR #51 contains the code/test changes. |
| 2026-07-10 | `TASK-054` information-architecture alignment merged through PR #52, adding routed discovery/list/detail/methodology flows and the revised 7-day Home. |
| 2026-07-10 | `ISS-011` resolved the final ES2020 Frontend build blocker in PR #53. ADR-037 closes Day 5 as a verified technical MVP milestone and defers deployment plus final presentation operations to TASK-020/TASK-021. |

## Constraints

- 5-day build window, 4-person team — see `../ORCHESTRATOR.md` and `../roadmap.md` for day-by-day allocation
- No accounts/login/saving/notifications/reports/team-sharing in MVP (PRD §6.5)
- No free-form AI analysis, no automated news matching, no wallet-level participant features (see `AGENTS.md` Absolute Restrictions)
- V3 runtime follows ADR-033 and is present on `main`; PR #53 must merge before
  its ES2020 compatibility repair and Day 5 closeout records reach `main`.
- No service deployment or final presentation capture is claimed by the Day 5
  technical closeout; those remain TASK-020 and TASK-021.
- Every data-bearing screen requires a data-as-of timestamp + interpretation-caution badge (PRD §8.10)
- Strict prohibited-wording policy — see `glossary.md` and `../standards.md`
