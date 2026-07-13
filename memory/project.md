<!--
Purpose:        Final project and operating-state snapshot
Owner:          Maintainers
Update Trigger: Runtime, deployment, contract, or safety-boundary change
Harness Version: 1.1
-->

# Project: Outlook AI Signals

_Last updated: 2026-07-13_

## Summary

Outlook AI Signals is an issue-monitoring dashboard built from public aggregate
Polymarket data. It presents reflected expectation values, observed changes,
time-series history, evidence-bounded briefings, data timestamps, and
interpretation cautions. It does not assert future results or present external
context as the explanation for an observed movement.

## Completion state

Application development is complete. The repository contains the implemented
Frontend, Backend, workers, database migrations, scheduled collector, production
Compose profile, public API contract, product/design documents, and final
presentation assets. There is no active development queue or planned feature
roadmap in the working documentation.

## Implemented system

| Area       | Final implementation                                                                                                                                                     |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Frontend   | React issue discovery, list, five-tab detail, chart, briefing, methodology, and scenario conversation with responsive and accessibility handling                         |
| API        | FastAPI issue/category/history reads, on-demand briefing requests, request status, validated-block SSE, and capability-scoped scenario sessions                          |
| Data       | Gamma collection, guarded CLOB history seed, append-only snapshots and metrics, fixed 24h/7d changes, caution levels, and change detection                               |
| Briefing   | V8 issue-centered evidence reconstruction, bounded context refresh, validated NDJSON blocks, cache fingerprints, polling fallback, and last-known-good behavior          |
| Scenario   | Issue-scoped 24-hour anonymous sessions, bearer-capability ownership, tool-free request workers, strict premise/output validation, authenticated SSE, and owner deletion |
| Storage    | PostgreSQL migrations 001-006 for market, evidence, report, generation, streaming-block, and ephemeral scenario state                                                    |
| Automation | Market-data-only GitHub Actions collection every four hours; scheduled collection does not invoke AI generation                                                          |
| Deployment | Docker Compose and Caddy configuration for the configured VPS; the production profile explicitly enables generation workers and scenario conversations                   |

## Permanent boundaries

- Public data is aggregate-only; wallet-level and individual-participant views
  are excluded.
- Every data-bearing screen retains a data-as-of timestamp and interpretation
  caution.
- Missing data, history, evidence, and sources remain absent rather than being
  fabricated.
- External material may be visibly attributed as context but cannot be presented
  as proof that it caused a movement.
- The public API process appends request state but does not construct an AI
  provider client.
- Only complete blocks that pass evidence, wording, numeric, leakage, Markdown,
  and schema validation are stored and replayed.
- Provider or validation failure never replaces the previous valid briefing.
- Schema, dependency, infrastructure, deployment, production-data, provider,
  and wording-policy changes remain governed by `AGENTS.md`.

## Accepted operating limitations

- A briefing request that remains queued across an unexpected process loss may
  require manual request-scoped worker recovery.
- A research provider may return no supported citation annotations; the safe
  result is a briefing with no external sources.
- Sparse or irregular CLOB history can limit change calculations.
- Volume is aggregate notional activity, not a participant count.
- The Frontend production bundle retains a non-blocking chart-library size
  warning.
- Python 3.11 is the supported local Backend runtime.
- Invalid enum query values use FastAPI's standard `422` response.
- The GitHub Actions workflow may emit a non-blocking action-runtime maintenance
  warning.

## Canonical documentation

- `README.md`: repository entry point and verification commands
- `AGENTS.md`: permanent maintenance and approval rules
- `docs/prd/`: product requirements and scope
- `docs/service-design/`: data, metric, AI, and safety behavior
- `docs/tech-design/`: architecture, schema, API, and worker design
- `docs/ux-design/`: screen, copy, caution, and rendering policy
- `memory/architecture.md`: concise implemented architecture
- `backend/API_CONTRACT.md`: active public API contract
- `standards.md` and `memory/glossary.md`: current engineering and wording rules
- `memory/decisions.md` and `tasks/completed.md`: retained development audit history

Historical task reports, role prompts, active/backlog ledgers, session handoffs,
and superseded report contracts are recoverable from Git history and are not
part of the final working documentation.
