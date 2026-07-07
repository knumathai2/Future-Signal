<!--
Purpose:        Technology decisions and rationale
Owner:          Backend Implementer (acting as Architect for this hackathon)
Update Trigger: New technology adopted, existing technology replaced
Harness Version: 1.1
-->

# tech-stack.md — Outlook Signals Technology Stack

_Last updated: 2026-07-07_
_Source: Technical Design §2 — this table mirrors it; Technical Design is the authoritative rationale document._

## Stack Overview

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | React + Vite + TypeScript + Tailwind CSS + Recharts | No SSR/SEO need for a hackathon demo; Vite gives instant reload; Tailwind lets one frontend person move fast; Recharts covers the line-chart-only requirement |
| Backend | Python + FastAPI | Same language as batch/data/AI work, so Backend and Data/AI roles share Pydantic models with zero translation cost; free OpenAPI docs double as the API spec |
| Database | PostgreSQL via Supabase or Neon (free tier) | Relational schema fits cleanly; managed hosting means zero ops setup time; web SQL console useful for hackathon debugging |
| Batch data collection | Python script(s) in the same repo as backend, scheduled via GitHub Actions | Reuses backend DB models/HTTP client; no separate worker infra needed at 30–50 market scale |
| AI report generation | Claude API (or OpenAI — whichever the team has ready key access to), template-constrained prompts | Structured-output-friendly; template constraint keeps token cost predictable and output safe |
| Data visualization | Recharts | Single dependency, line-chart-only per UX Design §6 |
| Authentication | None for MVP | PRD explicitly excludes accounts from hackathon scope |
| Deployment | Vercel (frontend) + Railway/Render (backend + batch) + Supabase/Neon (DB) | Generous free tiers, near-zero-config deploys from git push |
| Monitoring/logging | Structured stdout (JSON lines) + `data_collection_logs` DB table; Sentry free tier as should-have | Zero additional infra required; DB log table is queryable live during the demo |
| CI/CD | GitHub Actions | Batch-collector scheduling + basic lint/test workflow |

## Architecture Patterns

- **Structure**: Read-heavy, batch-fed dashboard — no live trading engine, no synchronous user write path in MVP (see Technical Design §1 diagram)
- **API style**: REST, JSON, versionless (`/api/...`, no `/v1` needed for hackathon), read-only except the internal report-trigger endpoint
- **State management**: None needed beyond React Query/fetch-on-mount for MVP — no client-side global store required at this screen count
- **Key architectural rule**: the API layer never calls the AI provider or Polymarket directly — it only reads from Postgres (Technical Design §3)

## Environments

| Environment | Purpose | Access |
|-------------|---------|--------|
| Local | Local development | localhost |
| Staging | Not planned separately for a 5-day hackathon — demo IS production | — |
| Production | Live demo for judging | Vercel URL (frontend) + Railway/Render URL (API) |

## Repository Structure

Working root: `AI Development Harness/`

```
AI Development Harness/
├── docs/
│   ├── prd/             # Product requirements, split by section
│   ├── service-design/  # Data/metrics/AI/signal spec
│   ├── tech-design/     # Architecture/schema/API/pipeline spec
│   └── ux-design/       # Screen flow/copy policy/safety guardrails
├── frontend/            # React + Vite + TS + Tailwind + Recharts
├── backend/             # FastAPI app + batch collector + AI report generation
└── .github/workflows/   # GitHub Actions (batch schedule, lint/test)
```
