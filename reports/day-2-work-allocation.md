# Day 2 Work Allocation — Outlook Signals

_Date: 2026-07-08_
_Owner: PM / Planner_
_Branch: `pm/TASK-031-day-2-allocation`_

## Summary

Day 2 is assigned around one goal: make the data pipeline, core read API, and home dashboard meet in a working local flow. P1 items stay opportunistic until the P0 data path is visible end to end.

Source scope:

- PRD §14 Day 2: data pipeline + core UI implementation.
- Day 1 closeout: API contract accepted, DB schema draft accepted but unapplied, frontend dummy flow ready.
- AGENTS.md approval gates: no shared/production DB writes, dependency additions, public API changes, infrastructure changes, or deployments without human approval.

## Day 2 Assignments

| ID | Owner | Branch | Status | First output needed | Handoff |
|---|---|---|---|---|---|
| TASK-031 | PM / Planner | `pm/TASK-031-day-2-allocation` | completed | User scenarios, judging Q&A seed, scope guardrails | All roles use this for Day 2 priorities |
| TASK-007 | Data/AI Implementer | `data-ai/TASK-007-fetch-normalize` | assigned | Normalized 30-50 market sample set | Feeds metrics, API fixtures, dashboard integration |
| TASK-008 | Data/AI Implementer + Backend | `data-ai/TASK-008-snapshot-metrics` | assigned | Snapshot + metric rows or local/dev-safe equivalent | Feeds `/api/issues` ranking and history |
| TASK-009 | Data/AI Implementer | `data-ai/TASK-009-shift-detection` | assigned | `expectation_shift` detections from 5pp threshold | Feeds detail response and chart markers later |
| TASK-010 | Backend Implementer | `backend/TASK-010-core-api` | assigned | Data-backed issue list/detail/history contract | Feeds frontend dashboard and detail path |
| TASK-012 | Frontend Implementer | `frontend/TASK-012-dashboard-ranking` | assigned | Dashboard cards aligned to API fields | Feeds demoable Home -> Detail flow |

## Recommended Work Order

### First block

- PM has completed the Day 2 scenario/Q&A seed and keeps the scope guardrails visible to each role.
- Data/AI starts `TASK-007` from the Day 1 Gamma/CLOB spike and produces normalized records before metric work.
- Backend starts `TASK-010` with contract preservation, stale contract wording cleanup if needed, and a read-path plan that can work from latest available data.
- Frontend starts `TASK-012` by reconciling dummy issue types with the accepted `/api/issues` response.

### Middle block

- Data/AI + Backend pair on `TASK-008` to make snapshot and metric outputs match the schema draft.
- Backend wires `/api/issues` ranking to latest metrics when data exists, or serves an honest static/last-known-good fallback while preserving `data_as_of`.
- Frontend swaps the dashboard data adapter from dummy-only to API-or-fallback without changing the safety copy pattern.

### Final block

- Data/AI adds `TASK-009` once `change_24h` is available.
- PM runs a short scope check: no P1 feature should enter unless `TASK-007`, `TASK-008`, `TASK-010`, and the dashboard path are usable.
- Reviewer pass is embedded: any changed user-facing copy needs wording lint, and every data-bearing screen needs timestamp + interpretation caution.

## Day 2 Guardrails

- Do not start AI report generation (`TASK-015`) today unless the data/API path finishes early and the PM explicitly reassigns it.
- Do not build category filtering, `/api/signals`, volatility/attention metrics, or empty-state polish ahead of the P0 path.
- Do not apply the schema draft to shared or production DB without separate human approval.
- Do not change the accepted public API contract without human approval; implementation details can change behind the same response shape.
- Do not add automated news matching or wallet-level/participant-level surfaces.

## PM Scenario Seed

Primary Day 2 demo story:

1. The user opens the dashboard and sees issues ranked by recent reflected-expectation change.
2. Each issue card shows the current value, 24h/7d movement, data reliability, and data-as-of timestamp.
3. The user opens one issue to inspect the chart/detail flow once Day 3 work lands.
4. The presenter explains that the product observes changes in public market data and attaches interpretation caution to every number.

Judging Q&A seed:

| Likely question | Day 2 answer shape |
|---|---|
| What is actually new here? | The product organizes public prediction-market data as an issue-monitoring dashboard, focused on change over time and caution context rather than outcome claims. |
| How do you avoid overclaiming? | The product uses reflected-expectation wording, data-as-of timestamps, interpretation-caution badges, and template-constrained summaries. |
| What happens if the live data path fails? | The API and frontend keep a static/last-known-good fallback path with honest timestamps. |
| Why no automated news matching? | Related events are manual-only for demo issues because automated matching can make timing look like causation. |
| Why only 30-50 markets? | That scope is enough for a credible hackathon demo while keeping normalization, quality checks, and safety review manageable. |
