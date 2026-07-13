<!--
Purpose:        Project milestones and feature planning
Owner:          PM / Planner
Update Trigger: Day completed, new feature request received, priorities changed
Harness Version: 1.1
-->

# roadmap.md — Outlook AI Signals Roadmap

_Last updated: 2026-07-11_
_Source: PRD §14 (5-Day Development Schedule) — this file tracks execution against it._

## Goal

Ship a genuinely working web MVP within 5 days that lets a user check today's most-changed issues (per Polymarket public data), open a detail chart, and read a template-based summary with interpretation-caution safeguards — without ever reading as a betting/trading/forecasting product.

## Milestones

### Day 1 — Scope + data validation + screen skeleton
- [x] PM: finalize MVP scope, define prohibited wording, draft presentation story
- [x] Frontend: wireframe dashboard/detail screens, start UI with dummy JSON
- [x] Backend: DB schema, API contract, server project setup
- [x] Data/AI: confirm Polymarket data structure (live spike against Gamma/CLOB), collect 10 sample markets
- **Deliverables**: screen structure, API contract doc, sample data, MVP scope doc, draft presentation key messages
- **Status note (2026-07-08)**: Day 1 is closed. Frontend dummy-data flow, accepted backend mock API contract, accepted-unapplied schema draft, and Polymarket samples exist. Durable outcomes are indexed in `tasks/completed.md`; temporary daily records remain available in Git history.

### Day 2 — Data pipeline + core UI
- [x] PM: organize user scenarios, prep judging-panel Q&A
- [x] Frontend: home dashboard, issue cards, ranking UI
- [x] Backend: market-list API, ranking API
- [x] Data/AI: calculate 24h/7d change, normalize 30–50 samples
- **Deliverables**: dashboard v1, ranking API, change-calculation data, candidate issue list for demo
- **Status note (2026-07-08)**: Day 2 is closed. The data pipeline, core read API, and dashboard v1 path are merged and verified in `tasks/completed.md`. P1/P2 items remain deferred unless the PM reassigns scope.

### Day 3 — Detail screen + chart + badges
- [x] PM: interpretation-caution text, disclaimer text, terminology revisions
- [x] Frontend: detail screen, time-series chart, tooltip
- [x] Backend: issue-detail API, price-history API
- [x] Data/AI: inflection-point threshold logic (±5pp), interpretation-caution badge logic
- **Deliverables**: issue detail screen, time-series chart, inflection-point markers, caution badge
- **Status note (2026-07-09)**: Day 3 is closed. The detail/chart/badge/notice
  path is merged through PR #27, no active Day 3 tasks remain, and the durable
  completion record is in `tasks/completed.md`. Shared/dev
  database schema application remains approval-gated; template summary
  generation moves to Day 4.

### Day 4 — Summary feature + demo flow complete
- [x] PM: draft presentation deck, write demo script
- [x] Frontend: UI polish, empty/loading/error states
- [x] Backend: stabilize API, fallback data handling
- [x] Data/AI: generate template summaries, link manual event candidates (3–5 curated issues)
- **Deliverables**: template summaries, 3 representative demo issues, stabilized demo flow, deck 70% complete
- **Status note (2026-07-10)**: Day 4 is closed. The summary/report path,
  related-event candidates, API fallback/readiness, report display states,
  demo/deck draft, and final `TASK-018` wording-safety lint are complete.
  Durable results are indexed in `tasks/completed.md`.

### Day 5 — Integration QA + technical MVP closeout
- [x] PM: coordinate the final v3 review and record the technical MVP closeout; final deck production, screenshots, rehearsal, and backup capture are deferred by ADR-037
- [x] Frontend: polish and responsive QA, ADR-033 dynamic report cards, TASK-054 information architecture, and the PR #53 ES2020 build repair
- [x] Backend: implement and verify the ADR-033 report runtime/read contract and preserve the existing fallback path; deployment is deferred
- [x] Data/AI: implement and review ADR-033 v3 report generation, safety validation, and representative stored-report evidence
- **Completed deliverables**: verified web MVP code, v3 report flow, demo/deck outline, demo scenario, fallback behavior, and Q&A draft
- **Deferred deliverables**: deployment, final presentation file, final screenshots, rehearsal, and backup video/screen captures (`TASK-020`, `TASK-021`)
- **Status note (2026-07-10)**: Day 5 is closed as a technical MVP milestone by
  explicit user direction. PR #53 merges the latest `main`, fixes the final
  ES2020 TypeScript build blocker, with the durable closeout recorded in
  `tasks/completed.md`. The branch passes Frontend typecheck, lint,
  report-parser regression, production build, and changed-file formatting, plus
  200 Backend tests and Ruff. PR #53 still requires the normal review/merge
  flow; deferred release and presentation work is not represented as completed.

## Backlog Ideas (Phase 2+ — do not build during the hackathon without HUMAN APPROVAL)

- Freer current summary plus a separate tool-free, issue-scoped scenario
  conversation. Planning and approval gates are in
  `reports/task-123-summary-scenario-chatbot-plan.md`; no runtime policy or
  implementation is active.
- Chart image export (content-creator tooling)
- Saved issues / watchlist (requires minimal account system)
- Change notifications (digest-style, neutral copy only)
- Weekly report generation
- Team sharing (B2B direction)
- Category-level and time-series participation trends
- Volatility / attention / momentum scores (P1 stretch if Day 3–4 time allows)
- Attention Spike / Unusual Market Activity signals (need historical baselines this hackathon won't have)
- Full multi-outcome market support

## Approved post-MVP program — TASK-056~065

The user approved the automated-context v4 program on 2026-07-11. Work runs
sequentially from policy lock through local/development backfill. It is bounded
to citation annotations returned by OpenRouter, deterministic and independent
AI verification, verified-only public output, evidence-linked v4 reports, an
append-only migration, and a cumulative OpenRouter budget of USD 100.

Deployment and production-database writes remain excluded. TASK-066~074 stay
inactive stretch work.

## Out of Scope (excluded outright, not just deferred)

- Unverified, source-less, or causal news-to-market matching. The narrowly
  approved TASK-056~065 v4 path is the only automated-context exception.
- Free-form AI analysis as a core feature (template-constrained only)
- Any wallet-level browsable/searchable participant view
- Any participant ranking, leaderboard, or "follow this trader" feature
- Bet placement, buy/sell/position recommendations, profit simulation
- Login, accounts, saving, notifications, reports, team sharing (all Phase 2+)
