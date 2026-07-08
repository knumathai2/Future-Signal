<!--
Purpose:        Project milestones and feature planning
Owner:          PM / Planner
Update Trigger: Day completed, new feature request received, priorities changed
Harness Version: 1.1
-->

# roadmap.md — Outlook Signals Roadmap

_Last updated: 2026-07-08_
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
- **Status note (2026-07-08)**: Day 1 is closed. Frontend dummy-data flow, accepted backend mock API contract, accepted-unapplied schema draft, and Polymarket samples exist. Full checkpoint: `reports/day-1-implementation-status.md`; closeout record: `reports/day-1-closeout-plan.md`.

### Day 2 — Data pipeline + core UI
- [ ] PM: organize user scenarios, prep judging-panel Q&A
- [ ] Frontend: home dashboard, issue cards, ranking UI
- [ ] Backend: market-list API, ranking API
- [ ] Data/AI: calculate 24h/7d change, normalize 30–50 samples
- **Deliverables**: dashboard v1, ranking API, change-calculation data, candidate issue list for demo

### Day 3 — Detail screen + chart + badges
- [ ] PM: interpretation-caution text, disclaimer text, terminology revisions
- [ ] Frontend: detail screen, time-series chart, tooltip
- [ ] Backend: issue-detail API, price-history API
- [ ] Data/AI: inflection-point threshold logic (±5pp), interpretation-caution badge logic
- **Deliverables**: issue detail screen, time-series chart, inflection-point markers, caution badge

### Day 4 — Summary feature + demo flow complete
- [ ] PM: draft presentation deck, write demo script
- [ ] Frontend: UI polish, empty/loading/error states
- [ ] Backend: stabilize API, fallback data handling
- [ ] Data/AI: generate template summaries, link manual event candidates (3–5 curated issues)
- **Deliverables**: template summaries, 3 representative demo issues, stabilized demo flow, deck 70% complete

### Day 5 — Integration QA + presentation finalized
- [ ] PM: finalize deck, prepare risk-response explanations, finalize demo script
- [ ] Frontend: polish demo screens, check responsiveness
- [ ] Backend: deploy, prepare dummy fallback for API outage
- [ ] Data/AI: check data errors, reinforce representative examples
- **Deliverables**: deployed MVP, presentation deck, demo scenario, backup video/screen captures, Q&A response sheet

## Backlog Ideas (Phase 2+ — do not build during the hackathon without HUMAN APPROVAL)

- Chart image export (content-creator tooling)
- Saved issues / watchlist (requires minimal account system)
- Change notifications (digest-style, neutral copy only)
- Weekly report generation
- Team sharing (B2B direction)
- Category-level and time-series participation trends
- Volatility / attention / momentum scores (P1 stretch if Day 3–4 time allows)
- Attention Spike / Unusual Market Activity signals (need historical baselines this hackathon won't have)
- Full multi-outcome market support

## Out of Scope (excluded outright, not just deferred)

- Automated news-to-market matching (causal-misinterpretation risk — manual curation only)
- Free-form AI analysis as a core feature (template-constrained only)
- Any wallet-level browsable/searchable participant view
- Any participant ranking, leaderboard, or "follow this trader" feature
- Bet placement, buy/sell/position recommendations, profit simulation
- Login, accounts, saving, notifications, reports, team sharing (all Phase 2+)
