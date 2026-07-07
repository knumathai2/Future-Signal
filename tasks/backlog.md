<!--
Purpose:        Prioritized list of tasks not yet started
Owner:          PM / Planner
Update Trigger: New task added, priority changed, day allocation changed
Harness Version: 1.1
-->

# Backlog — Outlook Signals

_Last updated: 2026-07-07_
_Seeded directly from PRD §14 and Technical Design §12 — this is the real Day 1 task list, not a placeholder._

## Must-Have (P0)

| ID | Task | Owner | Day | Size | Notes |
|----|------|-------|-----|------|-------|
| TASK-001 | Repo scaffold: create `/frontend` (Vite+React+TS+Tailwind) and `/backend` (FastAPI) | Backend Implementer | 1 | S | tech-stack.md layout |
| TASK-002 | DB schema creation (markets, market_outcomes, market_snapshots, market_metrics, issue_signals, ai_reports, related_events, data_collection_logs) | Backend Implementer | 1 | M | Technical Design §4 |
| TASK-003 | API contract draft (OpenAPI via FastAPI) | Backend Implementer + PM | 1 | S | Technical Design §5 |
| TASK-004 | Polymarket Gamma/CLOB live spike — confirm field structure, rate limits | Data/AI Implementer | 1 | M | Blocks schema finalization |
| TASK-005 | Wireframe dashboard/detail screens; start UI against dummy JSON | Frontend Implementer | 1 | M | Do not block on real API |
| TASK-006 | Finalize MVP scope doc + prohibited-wording policy | PM | 1 | S | Already drafted in PRD/UX Design — confirm and lock |
| TASK-007 | Batch collector: fetch + normalize (steps 1–2) | Data/AI Implementer | 1–2 | M | Technical Design §6 |
| TASK-008 | Batch collector: snapshot + metrics (steps 3–5) | Data/AI Implementer + Backend | 2 | M | Needs TASK-002, TASK-007 |
| TASK-009 | Signal detection (±5pp threshold) | Data/AI Implementer | 2 | S | Technical Design §8 |
| TASK-010 | `/api/issues`, `/api/issues/:id`, `/api/issues/:id/history` | Backend Implementer | 2 | M | Core read endpoints |
| TASK-011 | `/api/health` | Backend Implementer | 1 | XS | Trivial, do early |
| TASK-012 | Home dashboard UI (ranked issue cards) | Frontend Implementer | 2 | M | Depends on TASK-010 |
| TASK-013 | Issue detail UI + Recharts line chart | Frontend Implementer | 3 | M | Depends on `/history` endpoint |
| TASK-014 | Interpretation-caution badge component | Frontend Implementer | 3 | S | Reusable, per UX Design |
| TASK-015 | AI report generation function (template + banned-phrase filter) | Data/AI Implementer | 3–4 | L | Technical Design §9–10 — highest-risk task |
| TASK-016 | AI report display UI | Frontend Implementer | 4 | S | Depends on TASK-015 |
| TASK-017 | Disclaimer copy + footer + dedicated screen | Frontend Implementer + PM | 3–4 | S | UX Design §7–8 |
| TASK-018 | Copy/wording lint pass across all UI strings | PM | 4 | S | Against `../standards.md` Content Safety Lint |
| TASK-019 | 3–5 curated related events, manually entered | PM + Data/AI | 4 | S | `related_events` table |
| TASK-020 | Deploy all three services (Vercel, Railway/Render, Supabase/Neon) | Backend Implementer | 5 | M | |
| TASK-021 | Demo script + static-JSON fallback data | PM | 5 | S | Rehearsed backup for live-demo API failure |

## Should-Have (P1 — build only if Day 1–4 P0 finishes early)

| ID | Task | Owner | Day | Size | Notes |
|----|------|-------|-----|------|-------|
| TASK-022 | Category filter (frontend + `/api/categories`) | Frontend + Backend | 3–4 | S | |
| TASK-023 | `/api/signals` feed endpoint + UI | Backend + Frontend | 3–4 | M | |
| TASK-024 | Volatility/attention metrics | Data/AI Implementer | 3–4 | M | Needs more history accumulated |
| TASK-025 | Empty/loading/error states polish | Frontend Implementer | 4 | S | |
| TASK-026 | Sentry integration | Backend Implementer | 4–5 | S | |

## Nice-to-Have (P2 — do not build during the hackathon; see `../roadmap.md` Out of Scope)

| ID | Task | Notes |
|----|------|-------|
| TASK-027 | Search endpoint + UI | Only if all else done |
| TASK-028 | Responsive/mobile polish | |
| TASK-029 | Basic rate-limiting middleware | |
| TASK-030 | README / setup docs | |

## Size Reference

| Size | Estimated Effort |
|------|-------------------|
| XS | Under 1 hour |
| S | 1–4 hours |
| M | Half day to full day |
| L | 1–3 days |
| XL | 3+ days → must be decomposed (should not occur in a 5-day hackathon backlog) |
