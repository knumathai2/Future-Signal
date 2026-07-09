<!--
Purpose:        System design decisions and architecture structure
Owner:          Backend Implementer (acting Architect)
Update Trigger: New component added, design decision changed, dependency structure changed
Harness Version: 1.1
-->

# Architecture — Outlook Signals

_Last updated: 2026-07-09_
_Full detail: [Technical Design](../docs/tech-design/README.md) — this file is the working summary agents update as the build progresses._

## System Overview

A read-heavy, batch-fed dashboard built to achieve: surface Polymarket-based issue-change signals with strict interpretation-caution safeguards, in 5 days.

**Pattern**: no live trading engine, no synchronous user write path, no message queue/websockets/auth in MVP.

## Component Structure

```
Polymarket public APIs (Gamma + CLOB)
        |  scheduled fetch (GitHub Actions, every 1-4h)
        v
Batch Collector (Python) -- fetch -> normalize -> diff -> snapshot -> metrics -> signals -> logs -> (gated) AI reports
        |  writes
        v
PostgreSQL -- markets / market_outcomes / market_snapshots / market_metrics / issue_signals / ai_reports / related_events / data_collection_logs
        |  reads only
        v
FastAPI backend (read-only REST API) -- /api/issues /api/issues/:id /api/issues/:id/history /api/issues/:id/report ...
        |  HTTPS/JSON
        v
React + Vite frontend -- Home / Issue List / Detail / Chart / AI Report / Disclaimer
```

Key rule: **the API layer never calls the AI provider or Polymarket directly** — it only reads from Postgres. This decouples "is a report fresh" from "is a user waiting," and lets the API degrade to last-known-good data on failure.

## Data Flow

1. Batch collector fetches public Polymarket data for a curated 30–50 market list
2. Normalizes into Pydantic models, validates required fields, quarantines bad records (log + skip, never crash the run)
3. Diffs against the most recent snapshot, inserts a new `market_snapshots` row (append-only)
4. Computes `change_24h`/`change_7d`/`heat_score`/`confidence_level` into `market_metrics`
5. Evaluates the ±5pp threshold for `issue_signals` (cooldown-gated to avoid duplicate firing)
6. Day 4 active: qualifying markets (new expectation-shift row, no report yet, or stale >24h) get a new `ai_reports` row via template-constrained generation plus a safety filter
7. FastAPI serves the available read-only data; `TASK-039` wires the report endpoint to latest successful stored summaries while preserving the accepted empty state
8. React renders Home -> Detail -> Chart -> Summary; `TASK-016` now consumes the report endpoint and keeps caution context visible for success, loading, empty, and report-fetch failure states

## Design Decision Summary

> See `decisions.md` for full ADRs

| Decision | Choice | Date |
|----------|--------|------|
| Repo structure | Single monorepo (`/frontend`, `/backend`) | 2026-07-07 |
| Package managers | npm (frontend), pip (backend) | 2026-07-07 |
| CI/CD | GitHub Actions (batch schedule + lint/test) | 2026-07-07 |
| AI generation approach | Template-constrained, LLM only polishes phrasing, banned-phrase filter mandatory | 2026-07-07 (PRD §8.8, Service Design §6) |
| AI provider | OpenAI (`openai==2.44.0`, real `OpenAIReportClient`) | 2026-07-09 (ADR-022, human-approved) |
| Data update strategy | Append-only inserts, no upserts | 2026-07-07 (Technical Design §4.10) |
| Postgres driver | `psycopg[binary]` (psycopg3) | 2026-07-08 (ADR-007, human-approved) |
| Postgres URL compatibility | `psycopg2-binary==2.9.10` for provider-copied `postgresql://...` URLs | 2026-07-09 (ADR-023, human-approved) |
| Migration format (interim) | Plain SQL (`backend/migrations/*.sql`), not Alembic | 2026-07-08 (ADR-007) |

## Architecture Constraints

- Sequential batch script only — no queue/worker infra until report volume or latency demands it (Phase 2)
- API surface uses `issues`/`signals`/`reports`/`categories` naming — never `markets`/`bets`/`trades`/`positions`/`profits` in any public path, including internal code (Technical Design §5)
- No `users`/`watchlists`/wallet-level tables exist even in dormant form — schema itself is a policy signal (Technical Design §4.12)

## Implementation Status (2026-07-09 Day 4 Allocation)

- `/backend` scaffold exists (FastAPI app, `app/api/routes`, `app/core`, `app/db`, `app/schemas`) — see `backend/README.md`. App imports and boots cleanly; smoke-tested via a local venv (`pytest` + a live `uvicorn` request).
- `/frontend` scaffold exists (Vite + React + TS + Tailwind, npm scripts). `npm run lint` and `npm run build` pass locally in the Day 3 task sessions; production build still reports the known Recharts chunk-size warning tracked as TD-001.
- `GET /api/health` is live (mock/no DB dependency).
- `GET /api/issues`, `/api/issues/:id`, and `/api/issues/:id/history` read latest available snapshot/metric/history rows when a database is configured, and otherwise serve the documented static fallback with honest `data_as_of` timestamps (ADR-013). `/api/issues/:id/history` returns empty `points` when history is unavailable rather than fabricating a latest-point chart. `/api/issues/:id/report` reads the latest successful stored `ai_reports` row in live mode and preserves the accepted no-report-yet response when no successful report exists or the report read fails.
- DB schema draft is accepted (`backend/migrations/001_initial_schema.sql` + `backend/app/db/models.py`) and was applied to the currently configured development Supabase DB on 2026-07-09 after explicit human approval. Tables are present but empty, so live issue reads still fall back until snapshot/metric rows are inserted. Applying schema changes to any other shared or production DB remains approval-gated.
- `TASK-007` collector now fetches active Gamma events, validates binary market candidates, writes 50 normalized sample records, and quarantines skipped candidates with structured reasons. Per ADR-014, the artifact emits a display-safe `description: str` and omits raw source descriptions.
- `TASK-008` snapshot/metrics logic computes `change_24h`, `change_7d`, placeholder `heat_score`, and confidence levels through a local/dev-safe path. `TASK-036` adds MVP `caution_low_activity` and `caution_high_volatility` thresholds documented in ADR-019.
- `TASK-009` expectation-shift detector inserts `expectation_shift` rows for the MVP ±5pp threshold with a 24h cooldown and no evaluation for insufficient data.
- `TASK-012` dashboard v1 reads the backend API, keeps a static fallback path, and displays data-as-of timestamps plus caution badges on data-bearing views.
- `TASK-035` verified the existing detail/history read paths for the Day 3 chart/marker flow without changing accepted response shapes.
- `TASK-013` hardened the issue detail chart: 24h/7d/30d windows require baseline-covered history, tooltip values include timestamp/value/previous-point pp change, and markers consume API-provided rows when present.
- `TASK-014` aligned caution badge labels, visual treatment, accessibility labels, and placement across dashboard and detail surfaces.
- `TASK-017` added shared brief caution copy, reusable footer copy, and a dedicated in-app information notice surface without adding a routing dependency.
- `TASK-038` assigned Day 4 active work: `TASK-015` template report generation and safety filter, `TASK-039` report API/fallback readiness, `TASK-016` report display UI, `TASK-019` manual event candidates, `TASK-040` demo/deck draft, and `TASK-018` final wording lint.
- `TASK-015` implemented `backend/app/core/ai_report.py` (fixed §10.1/§10.2 prompt templates, `OpenAIReportClient`, strict 5-field schema parse, banned-phrase/pattern safety filter) and `backend/app/core/ai_report_batch.py` (regeneration eligibility, top-10-by-heat_score cap, retry-once-then-fail, filter-failure discard-without-retry - previous successful `ai_reports` row always stays served on any failure). Per ADR-022, OpenAI is the real provider (no key configured in this environment, so no live call has executed yet).
- `TASK-039` is now complete via PR #29 follow-up: the report endpoint serves latest successful stored `ai_reports` rows in live mode and keeps the accepted empty state for absent/failed reads.
- `TASK-016` is complete: the frontend detail flow fetches `/api/issues/{id}/report` alongside issue detail and 30d history, renders the five fixed report sections when a stored report is available, and keeps neutral loading, `not_yet_generated`, and report-failure states isolated to the summary card with nearby data-as-of timing and caution context.
- Backend local setup should use Python 3.11 on this machine; the default Python 3.9 runtime could not install the pinned `psycopg[binary]==3.2.3` binary package.
- Day 4 is active from this baseline. Any shared or production schema application, paid external AI call, public API shape change, deployment, or infrastructure change remains separately approval-gated.
