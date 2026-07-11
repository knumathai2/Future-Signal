<!--
Purpose:        Prioritized list of tasks not yet started
Owner:          PM / Planner
Update Trigger: New task added, priority changed, day allocation changed
Harness Version: 1.1
-->

# Backlog — Outlook Signals

_Last updated: 2026-07-10_
_Deferred and post-hackathon backlog after the Day 5 technical closeout; active work lives in `tasks/active.md`._

Day 2 allocation moved `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`, and `TASK-012` to `tasks/active.md`. `TASK-031` was created directly from PRD §14's Day 2 PM work because that PM task was missing from the original backlog.

Day 3 allocation moved `TASK-013`, `TASK-014`, and `TASK-017` to
`tasks/active.md`. `TASK-034` was created directly as the PM allocation task,
and `TASK-035`/`TASK-036` were created directly in `tasks/active.md` to cover
the Day 3 backend and Data/AI handoffs that were missing from the original
backlog.

Day 4 allocation moved `TASK-015`, `TASK-016`, `TASK-018`, and `TASK-019` to
`tasks/active.md`. `TASK-038` was created directly as the PM allocation task,
and `TASK-039`/`TASK-040` were created directly in `tasks/active.md` to cover
the Day 4 backend fallback/readiness and PM deck/demo work that were present in
PRD section 14 but missing from the original backlog.

## Deferred Release and Presentation Work

ADR-037 closes the technical MVP milestone without claiming these operational
deliverables are finished. They can be resumed independently after the
hackathon closeout.

| ID | Task | Owner | Original Day | Size | Resume condition | Notes |
|----|------|-------|--------------|------|------------------|-------|
| TASK-020 | Deploy the approved service set | Backend Implementer | 5 | M | Explicit deployment approval and target-platform access | No deployment was performed during Day 5 closeout. |
| TASK-021 | Finalize presentation assets, rehearse the demo, and capture the backup sequence | PM | 5 | S | Presentation work is resumed | The outline, script, Q&A draft, and static fallback behavior exist; the final deck, screenshots, rehearsal, and backup capture remain. |

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

## Proposed Automated Context Program — blocked pending TASK-056 approval

This program is documented by `TASK-055` for a one-person, AI-assisted,
20-hour implementation. It is not active work. The current constitution and
product documents still exclude automated public context matching. `TASK-056`
must receive explicit user approval before any implementation task moves to
`tasks/active.md`.

| ID | Task | Owner | Branch | Hours | Dependency | Notes |
|----|------|-------|--------|------:|------------|-------|
| TASK-056 | Approve automated-context policy and v4 contract | PM / Planner | `pm/TASK-056-auto-context-policy` | 1.0 | TASK-055 | Human approval gate for policy, provider budget, schema, API, and local/dev writes. |
| TASK-057 | Add automated-context storage schema | Backend Implementer | `backend/TASK-057-context-schema` | 1.5 | TASK-056 | Append `002_context_candidates.sql`; never edit the existing migration. |
| TASK-058 | Build OpenRouter web-research client | Data/AI Implementer | `data-ai/TASK-058-context-research` | 2.5 | TASK-056 | Parse only API `url_citation` annotations; no DB write. |
| TASK-059 | Build deterministic and independent-AI verification | Data/AI Implementer | `data-ai/TASK-059-context-verification` | 2.5 | TASK-058 | Official single-source or independent multi-source hard gate. |
| TASK-060 | Connect context research to the scheduled batch | Data/AI Implementer | `data-ai/TASK-060-context-batch` | 2.0 | TASK-057~059 | Signal/heat/staleness selection, append-only storage, failure isolation. |
| TASK-061 | Generate evidence-grounded v4 reports | Data/AI Implementer | `data-ai/TASK-061-evidence-report-v4` | 2.0 | TASK-060 | Every metric/context sentence references stored evidence. |
| TASK-062 | Serve the v4 context/report API | Backend Implementer | `backend/TASK-062-context-report-api` | 2.0 | TASK-057, TASK-061 | Strict response, verified candidates only, legacy exclusion. |
| TASK-063 | Build the change-episode UI | Frontend Implementer | `frontend/TASK-063-change-episode-ui` | 2.5 | TASK-062 | Chart, context, sources, summary, timing, and caution on one surface. |
| TASK-064 | Review the automated-context integration | Reviewer | `review/TASK-064-auto-context-integration` | 2.0 | TASK-057~063 | Contract, evidence, wording, responsive, and fail-closed review. |
| TASK-065 | Run local/dev backfill and record demo evidence | Data/AI Implementer + PM | `data-ai/TASK-065-context-backfill` | 2.0 | TASK-064 | Guarded provider/DB run within the approved budget; deployment remains separate. |

Exact scope, data contracts, file ownership, acceptance criteria, commands,
handoffs, and stop conditions are in
`reports/task-055-automated-context-execution-plan.md`.

## Proposed Automated Context Stretch Program — after TASK-065

These tasks are optional and remain inactive. Start them only after the core
20-hour program passes `TASK-064` and `TASK-065`, and only within the policy,
schema, API, provider, and local/dev-write approvals recorded by `TASK-056`.
Any new schema/API surface outside that approval requires an addendum before
implementation.

| ID | Task | Owner | Branch | Hours | Dependency | Notes |
|----|------|-------|--------|------:|------------|-------|
| TASK-066 | Build an offline context-evaluation harness | Reviewer + Data/AI Implementer | `review/TASK-066-context-evaluation` | 3.0 | TASK-065 | Replay citations/model output and gate known URL, conflict, duplicate, and evidence failures. |
| TASK-067 | Add a versioned source-policy registry and official-source adapters | Data/AI Implementer + PM | `data-ai/TASK-067-source-registry` | 3.0 | TASK-066 | Move source classification out of model judgment; honor `resolutionSource`. |
| TASK-068 | Add claim-level support and contradiction checks | Data/AI Implementer | `data-ai/TASK-068-context-contradiction` | 3.0 | TASK-066, TASK-067 | Withhold candidates whose dates, states, or supported claims conflict. |
| TASK-069 | Revalidate candidate links, content hashes, and expiry | Backend + Data/AI Implementer | `backend/TASK-069-context-revalidation` | 2.0 | TASK-068 | Append-only checks; stale/invalid candidates leave the public path. |
| TASK-070 | Backfill and cluster 7d/30d historical change episodes | Data/AI Implementer | `data-ai/TASK-070-historical-context` | 3.0 | TASK-068, TASK-069 | Deterministic episode clustering and idempotent historical research. |
| TASK-071 | Add bounded multilingual official-source research | Data/AI Implementer | `data-ai/TASK-071-multilingual-context` | 3.0 | TASK-067, TASK-070 | English plus at most one local language; citation-first translation checks. |
| TASK-072 | Add source provenance and verification-path UI | Frontend + Backend Implementer | `frontend/TASK-072-context-provenance-ui` | 2.5 | TASK-070, TASK-071 | Source title/domain/date and episode timeline without internal model scores. |
| TASK-073 | Add search cache, provider-failure controls, and observability | Backend + Data/AI Implementer | `backend/TASK-073-context-reliability` | 2.5 | TASK-069, TASK-072 | TTL cache, circuit breaker, usage metrics, and last-good preservation. |
| TASK-074 | Build a cross-issue event graph | Data/AI + Backend Implementer | `data-ai/TASK-074-cross-issue-context` | 3.0 | TASK-068, TASK-070, TASK-073 | Reuse one event across markets while keeping per-market verification independent. |

The stretch sequence totals 25 additional hours. Prioritized stop points are
3h, 6h, 9h, 11h, 14h, 17h, 19.5h, 22h, and 25h. Full task packets are in
`reports/task-055-automated-context-stretch-plan.md`.

## Size Reference

| Size | Estimated Effort |
|------|-------------------|
| XS | Under 1 hour |
| S | 1–4 hours |
| M | Half day to full day |
| L | 1–3 days |
| XL | 3+ days → must be decomposed (should not occur in a 5-day hackathon backlog) |
