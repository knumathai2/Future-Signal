<!--
Purpose:        System design decisions and architecture structure
Owner:          Backend Implementer (acting Architect)
Update Trigger: New component added, design decision changed, dependency structure changed
Harness Version: 1.1
-->

# Architecture — Outlook Signals

_Last updated: 2026-07-08_
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
6. Qualifying markets (new signal, no report yet, or stale >24h) get a new `ai_reports` row via template-constrained LLM call + banned-phrase filter
7. FastAPI serves all of the above read-only; frontend renders Home → Detail → Chart → Report

## Design Decision Summary

> See `decisions.md` for full ADRs

| Decision | Choice | Date |
|----------|--------|------|
| Repo structure | Single monorepo (`/frontend`, `/backend`) | 2026-07-07 |
| Package managers | npm (frontend), pip (backend) | 2026-07-07 |
| CI/CD | GitHub Actions (batch schedule + lint/test) | 2026-07-07 |
| AI generation approach | Template-constrained, LLM only polishes phrasing, banned-phrase filter mandatory | 2026-07-07 (PRD §8.8, Service Design §6) |
| Data update strategy | Append-only inserts, no upserts | 2026-07-07 (Technical Design §4.10) |
| Postgres driver | `psycopg[binary]` (psycopg3) | 2026-07-08 (ADR-007, human-approved) |
| Migration format (interim) | Plain SQL (`backend/migrations/*.sql`), not Alembic | 2026-07-08 (ADR-007) |

## Architecture Constraints

- Sequential batch script only — no queue/worker infra until report volume or latency demands it (Phase 2)
- API surface uses `issues`/`signals`/`reports`/`categories` naming — never `markets`/`bets`/`trades`/`positions`/`profits` in any public path, including internal code (Technical Design §5)
- No `users`/`watchlists`/wallet-level tables exist even in dormant form — schema itself is a policy signal (Technical Design §4.12)

## Backend Implementation Status (2026-07-08)

- `/backend` scaffold exists (FastAPI app, `app/api/routes`, `app/core`, `app/db`, `app/schemas`) — see `backend/README.md`. App imports and boots cleanly; smoke-tested via a local venv (`pytest` + a live `uvicorn` request).
- `/frontend` scaffold exists (Vite + React + TS + Tailwind, npm scripts). `npm run lint` and `npm run build` pass locally as of 2026-07-08; production build still reports the known Recharts chunk-size warning tracked as TD-001.
- `GET /api/health` is live (mock/no DB dependency).
- `GET /api/issues`, `/api/issues/:id`, `/api/issues/:id/history`, `/api/issues/:id/report`, `/api/categories` exist but return **hardcoded sample data**, not live Postgres reads — see `backend/API_CONTRACT.md`; ADR-008 accepts the no-report-yet response shape.
- DB schema draft is accepted (`backend/migrations/001_initial_schema.sql` + `backend/app/db/models.py`) but **not applied to any database** — human approval still required before applying, per `AGENTS.md` and ADR-011.
- `TASK-007` collector now fetches active Gamma events, validates binary market candidates, writes 50 normalized sample records, and quarantines skipped candidates with structured reasons. Per ADR-014, the artifact emits a display-safe `description: str` and omits raw source descriptions.
- Backend local setup should use Python 3.11 on this machine; the default Python 3.9 runtime could not install the pinned `psycopg[binary]==3.2.3` binary package.
- Next backend step after Day 2 assignment: `TASK-010` wires `app/api/routes/issues.py`/`categories.py` toward latest available data while preserving the accepted public contract. Any shared or production schema application remains separately approval-gated.
