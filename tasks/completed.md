<!--
Purpose:        Archive of completed tasks (accumulate; do not delete)
Owner:          Implementer roles / PM
Update Trigger: Task completed
Harness Version: 1.1
-->

# Completed Tasks — Outlook Signals

_Last updated: 2026-07-08_

| ID | Task | Completed | Owner | Notes |
|----|------|-----------|-------|-------|
| — | AI Development Harness v1.1 initial setup | 2026-07-07 | PM | Standard tier, monorepo, npm+pip, GitHub Actions |
| TASK-001 | Repo scaffold: `/frontend` + `/backend` project shells | 2026-07-08 | Backend Implementer | `backend/TASK-001-repo-scaffold`. FastAPI app import-smoke-tested; frontend hand-scaffolded (npm/node unavailable in this environment, not run). |
| TASK-002 | DB schema draft for MVP tables | 2026-07-08 | Backend Implementer | Draft accepted as a Day 1 artifact in ADR-011. Migration remains unapplied; applying schema changes to any shared or production database still requires separate human approval. |
| TASK-003 | API contract draft and response-shape agreement | 2026-07-08 | Backend Implementer + PM | PM/Frontend sign-off recorded. Public route names and response fields are accepted for Day 2 implementation dependency; ADR-008 accepts `200 {"status": "not_yet_generated"}` for the no-report-yet response. |
| TASK-011 | Add `GET /api/health` endpoint | 2026-07-08 | Backend Implementer | `backend/TASK-011-health-endpoint`. Verified via pytest + a live uvicorn request; appears in `/openapi.json`. |
| TASK-004 | Polymarket Gamma/CLOB live spike | 2026-07-08 | Data/AI Implementer | Gamma fields, pagination, rate-limits, CLOB history shape documented; samples saved |
| TASK-005 | Wireframe dashboard/detail screens; start UI against dummy JSON | 2026-07-08 | Frontend Implementer | React/Vite/Tailwind/Recharts UI implemented with dashboard, issue cards, detail view, caution badges, data-as-of timestamps, dummy data contract, and loading/empty/error states. |
| TASK-006 | Finalize MVP scope doc, prohibited-wording policy, and Day 1 presentation story | 2026-07-08 | PM | P0 scope remains locked, wording policy references `standards.md` and `memory/glossary.md`, Day 1 implementation status recorded in `reports/day-1-implementation-status.md`, and demo message stays in issue-monitoring framing. |
| TASK-031 | Organize Day 2 user scenarios, judging Q&A, and scope guardrails | 2026-07-08 | PM | Day 2 active work assigned to `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`, and `TASK-012`; sequencing, PM scenario seed, and judging Q&A seed recorded in `reports/day-2-work-allocation.md`. |
| TASK-012 | Home dashboard UI (ranked issue cards) | 2026-07-08 | Frontend Implementer | Integrated categories and issues with backend routes, added UI filters/sort options, and implemented error-to-stale-dummy fallback. |
