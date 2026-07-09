<!--
Purpose:        Prioritized list of tasks not yet started
Owner:          PM / Planner
Update Trigger: New task added, priority changed, day allocation changed
Harness Version: 1.1
-->

# Backlog — Outlook Signals

_Last updated: 2026-07-09_
_Remaining backlog after Day 3 assignment; active work lives in `tasks/active.md`._

Day 2 allocation moved `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`, and `TASK-012` to `tasks/active.md`. `TASK-031` was created directly from PRD §14's Day 2 PM work because that PM task was missing from the original backlog.

Day 3 allocation moved `TASK-013`, `TASK-014`, and `TASK-017` to
`tasks/active.md`. `TASK-034` was created directly as the PM allocation task,
and `TASK-035`/`TASK-036` were created directly in `tasks/active.md` to cover
the Day 3 backend and Data/AI handoffs that were missing from the original
backlog.

## Must-Have (P0)

| ID | Task | Owner | Day | Size | Notes |
|----|------|-------|-----|------|-------|
| TASK-015 | AI report generation function (template + banned-phrase filter) | Data/AI Implementer | 3–4 | L | Technical Design §9–10 — highest-risk task |
| TASK-016 | AI report display UI | Frontend Implementer | 4 | S | Depends on TASK-015 |
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
