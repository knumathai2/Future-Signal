# Technical Architecture Design: Outlook Signals MVP

Document version: v1.0
Date: 2026-07-07
Companion to: [PRD](../prd/README.md) (hackathon PRD, v1.1, 5-day / 4-person team), [Service Design](../service-design/README.md) (data/metrics/AI/signal spec), [UX Design](../ux-design/README.md) (screens/copy/UX policy)
Purpose: Translate the product and data design into a buildable stack, schema, API, batch pipeline, and AI report architecture for the 5-day hackathon team, with a clear line to Phase 2.

**Technical assumption**: the team is the same 4 people as PRD §13 (PM/planning, Frontend, Backend/API/DB, Data/AI). This document picks a stack that minimizes the number of languages/frameworks that team has to juggle simultaneously, since context-switching cost is the real constraint in a 5-day build, not raw technical capability.

---

## 1. Technical Design Summary

The system is a **read-heavy, batch-fed dashboard**: there is no live trading engine, no user-submitted financial data, and no synchronous write path from users at all in MVP (no accounts, no watchlist yet). This shape is the single biggest simplifying fact for the architecture — it means the whole system can be built as:

```
Polymarket public APIs --> Batch collector (scheduled) --> Postgres --> Read-only REST API --> Frontend
                                          |
                                          +--> Metric calc + signal detection --> AI report generation (async, cost-gated)
```

No message queue, WebSocket service, or user-auth system is required for the
hackathon MVP. TASK-117 adds a narrow server-sent event read path over
append-only validated briefing blocks; it reuses FastAPI, Postgres, and the
existing worker and does not add real-time infrastructure.

---

## 2. Recommended Technology Stack

| Layer | Recommendation | Why suitable for MVP | Difficulty | Scalability | Alternatives | Final call |
|---|---|---|---|---|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS + Recharts | No SSR needed (no SEO requirement for a hackathon demo), Vite gives near-instant dev reload, Tailwind lets one frontend person move fast without a design system, Recharts covers the line-chart-only requirement from UX Design §3.4 out of the box | Low | Fine up to Phase 2 personalization; would reconsider only if SEO/marketing pages are added later | Next.js (adds SSR complexity not needed yet), plain HTML/Chart.js (too slow to build a multi-screen flow) | **React + Vite + TS + Tailwind + Recharts** |
| Backend | Python + FastAPI | Same language as the batch/data/AI work, so the Data/AI and Backend roles (PRD §13) can read each other's code and share Pydantic models with zero translation cost; FastAPI gives free OpenAPI docs, which doubles as the API spec deliverable in Section 5 | Low–Medium | Fine for MVP traffic (read-mostly, dozens of markets); would move to a proper task queue only if report generation volume grows | Node/Express (would force a second language for the Data role, which is already doing Python-style data wrangling) | **FastAPI** |
| Database | PostgreSQL, hosted on Supabase or Neon (free tier) | Relational schema fits the data cleanly (Section 4), managed hosting means zero ops setup time, both offer instant provisioning and a web SQL console useful for hackathon debugging | Low | Comfortably handles Phase 2 volumes (thousands of snapshot rows/day); revisit partitioning only well past MVP scale | SQLite (simpler locally, but painful for a hosted multi-person team to share state), MongoDB (schema here is genuinely relational — a document DB adds friction, not speed) | **Postgres via Supabase/Neon** |
| Batch data collection | Python script(s), same codebase/repo as the backend, run on a schedule via a hosting-platform cron (Railway/Render cron job) or GitHub Actions scheduled workflow | Reuses the backend's DB models and HTTP client setup; a scheduled workflow needs no separate worker infrastructure | Low | Fine until collection frequency needs sub-minute granularity; a dedicated worker/queue is a Phase 2 concern | Airflow/Prefect (correct answer at scale, total overkill for 30–50 markets over 5 days) | **Python script + platform cron / GitHub Actions schedule** |
| AI report generation | Claude API (Anthropic), called from the same Python backend, template-constrained prompts (Section 10) | Structured-output-friendly, and using the same provider family as this document's own generation keeps the guardrail language and safety framing consistent; template constraint keeps token cost predictable | Low–Medium | Cost is gated by "only regenerate on meaningful change" (Section 9), not by raw request volume | OpenAI API (equally valid choice; pick whichever the team already has API-key access to — this is a swappable implementation detail, not an architectural one) | **Claude API (or OpenAI, whichever the team has ready access to) via a single internal `generate_report()` function** |
| Data visualization | Recharts (already covered above) | Single dependency, matches the "line chart only, no candlestick" rule from UX Design §6 | Low | Fine | Chart.js, Visx | **Recharts** |
| Authentication | **None for MVP** | PRD explicitly excludes accounts from the hackathon scope; building auth now is pure opportunity cost | N/A | Phase 2 needs it only for watchlist — recommend a lightweight magic-link or anonymous device-id approach then, not full OAuth | Supabase Auth (good Phase 2 default, since Supabase is already the DB choice) | **None now; Supabase Auth in Phase 2 if watchlist ships** |
| Deployment | Frontend on Vercel or Netlify (static build); backend + batch script on Railway or Render (single small always-on or cron-triggered service); DB on Supabase/Neon | All four have generous free tiers, near-zero-config deploys from a git push, and no server management | Low | Fine for MVP; a real scale-up would separate the batch worker from the API service, but one small service can do both for 30–50 markets | Self-hosted VPS (more control, much more setup time — wrong tradeoff for 5 days) | **Vercel (frontend) + Railway/Render (backend+batch) + Supabase/Neon (DB)** |
| Monitoring and logging | Structured stdout logging (JSON lines) captured by the hosting platform's built-in log viewer, plus the `data_collection_logs` DB table (Section 4) as the source of truth for pipeline health; optionally Sentry free tier for error capture | Zero additional infrastructure; the DB log table is queryable during the demo if something goes wrong | Low | A dedicated observability stack (Datadog, Grafana) is unnecessary until there's real production traffic | Sentry (recommended as the one "nice-to-have" addition — free tier, 10-minute setup, catches unhandled exceptions in both API and batch job) | **Platform logs + `data_collection_logs` table, + Sentry as should-have** |

---

## 3. System Architecture Overview

```
                          ┌────────────────────────┐
                          │   Polymarket public     │
                          │  Gamma API / CLOB API   │
                          └────────────┬────────────┘
                                       │ scheduled fetch
                                       v
                        ┌───────────────────────────────┐
                        │      Batch Collector (Python)   │
                        │  fetch -> normalize -> diff ->  │
                        │  snapshot -> metrics -> signals │
                        │  -> logs -> (gated) AI reports  │
                        └───────────────┬─────────────────┘
                                       │ writes
                                       v
                        ┌───────────────────────────────┐
                        │         PostgreSQL              │
                        │ markets / snapshots / metrics /  │
                        │ signals / ai_reports / logs      │
                        └───────────────┬─────────────────┘
                                       │ reads only
                                       v
                        ┌───────────────────────────────┐
                        │     FastAPI backend (read API)  │
                        │  /issues /signals /reports ...  │
                        └───────────────┬─────────────────┘
                                       │ HTTPS/JSON
                                       v
                        ┌───────────────────────────────┐
                        │   React + Vite frontend          │
                        │ Home / Issue List / Detail /...  │
                        └───────────────────────────────┘
```

Key architectural property: **the API layer never calls the AI provider or Polymarket directly.** It only reads from Postgres. This keeps API latency predictable and completely decouples "is a report fresh" from "is a user waiting for a response" — the report is either already there or it isn't, and if it isn't, the API returns the last good one with its own timestamp (mirrors the "last known good data" fallback already defined in PRD §8.1).

---
