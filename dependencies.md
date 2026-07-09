<!--
Purpose:        External dependency tracking and version constraints
Owner:          Backend Implementer / Frontend Implementer
Update Trigger: Dependency added, removed, or version changed (HUMAN APPROVAL required)
Harness Version: 1.1
-->

# dependencies.md — Outlook Signals Dependencies

_Last updated: 2026-07-09_

## Core Dependencies — Frontend

| Package | Purpose |
|---------|---------|
| react, react-dom | UI framework |
| vite | Build tool / dev server |
| typescript | Type safety |
| tailwindcss | Styling |
| recharts | Line chart rendering (24h/7d/30d, inflection markers) |

## Core Dependencies — Backend

| Package | Purpose |
|---------|---------|
| fastapi | Read-only REST API |
| uvicorn | ASGI server |
| pydantic | Request/response models, data validation |
| sqlalchemy (or equivalent) | Postgres ORM/query layer |
| psycopg[binary] | Postgres driver paired with SQLAlchemy — approved 2026-07-08 (TASK-001, human approval) |
| python-dotenv | Local-dev `.env` loading only, not used in deployed environments — approved 2026-07-08 (TASK-001, human approval) |
| httpx or requests | Polymarket Gamma/CLOB API calls |
| openai==2.44.0 | Template-constrained AI report generation client — approved 2026-07-09 for TASK-015 in ADR-022 (human approval; no live calls unless `OPENAI_API_KEY` is configured) |

## Dev Dependencies

| Package | Purpose |
|---------|---------|
| eslint / prettier | Frontend lint/format |
| ruff | Backend lint/format |
| pytest | Backend tests (change-calc, threshold, banned-phrase filter) |

## External Services / APIs

| Service | Purpose | Auth | Notes |
|---------|---------|------|-------|
| Polymarket Gamma API | Market/event metadata, categories, volume, liquidity, dates | Public, no auth documented as required | Validate field structure on Day 1 spike (Technical Design §17) |
| Polymarket CLOB API | Order book, trade prices, `prices-history` | Public | Resolution/retention varies by market age — thin markets have gappy history |
| OpenAI API | Template-phrasing pass for AI report generation only, never free-form | API key | Provider and package approved 2026-07-09 in ADR-022; cost-gated by missing-key default, signal/staleness regeneration, and batch cap (Technical Design §9) |
| Supabase or Neon | Managed PostgreSQL hosting | Connection string / API key | Pick one on Day 1, do not evaluate both mid-build |
| Vercel | Frontend hosting | Git-connected | Auto-deploy on push |
| Railway or Render | Backend + batch collector hosting | Git-connected | Auto-deploy on push; also hosts the cron-triggered batch job |
| Sentry (should-have) | Error capture | API key | Optional — only if a role finishes must-haves early |

## Explicitly excluded dependencies (do not add without HUMAN APPROVAL + PM sign-off)

- Any auth/accounts library (Supabase Auth, NextAuth, etc.) — no login in hackathon MVP
- Any message queue / task runner (Celery, RQ, Airflow, Prefect) — sequential batch script is sufficient at 30–50 markets
- Candlestick/financial charting libraries — line-chart-only per UX Design §3.4

## Version Policy

- Major upgrades: HUMAN APPROVAL + full manual demo-flow retest required
- Minor / patch: Reviewer sign-off then proceed
- Security patches: Apply immediately, Reviewer reviews after
- Given the 5-day window: avoid any dependency upgrade during the hackathon unless it fixes a blocking bug

## Temporary Audit Decisions

- 2026-07-08 / PR #6: Keep frontend on the approved Vite 5.x major range and temporarily accept the Vite/esbuild dev-server audit warning. Clearing it requires a Vite major upgrade, which is deferred to a separate dependency-maintenance task with explicit approval and full manual demo-flow retest (ADR-010).
