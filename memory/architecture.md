<!--
Purpose:        Current implemented architecture and invariants
Owner:          Backend Implementer / Data-AI Implementer
Update Trigger: Implemented architecture or boundary change
Harness Version: 1.1
-->

# Architecture — Outlook Signals

_Last updated: 2026-07-12_

## System overview

```text
Polymarket Gamma API
        |
        v
four-hour collection workflow
  fetch -> normalize -> snapshots -> metrics -> signals -> collection log
        |
        v
PostgreSQL <-> FastAPI <-> React/Vite
        ^          |
        |          v
        +---- on-demand generation request
                    |
                    v
              isolated v8 worker
      stored evidence -> optional context refresh -> NDJSON writer
                    |
                    v
       validated blocks -> final report -> request outcome
                    |
                    v
              SSE replay / polling
```

## Runtime boundaries

### Market collection

- `.github/workflows/four-hour-collection.yml` runs at minute 17 every four
  UTC hours and supports manual dispatch.
- The job receives `DATABASE_URL` only and explicitly skips report and context
  stages.
- Gamma data is normalized to active binary issues. Invalid records are
  quarantined without stopping the full run.
- `market_snapshots`, `market_metrics`, signals, and collection logs are
  append-only. Only market status and last-seen metadata update in place.
- `backend/app/core/historical_seed.py` is a guarded local/development-only CLOB
  history path; it never rewrites existing snapshots.

### Public API

- Issue list/detail/history reads are market- and time-bounded and degrade to
  timestamped static fallback states when configured data is unavailable.
- `POST /api/issues/{id}/report/generate` appends or joins an immutable
  fingerprinted request. The API does not construct a provider client.
- Request status reads one request plus its latest append-only event.
- The SSE endpoint replays only already validated blocks for the active
  request attempt and supports `Last-Event-ID`.

### V8 briefing worker

- A local/development child worker claims queued or expired-running requests
  with bounded leases.
- Input fingerprints cover prompt, policy, input schema, metric/snapshot,
  definition, context, and source evidence.
- Context refresh accepts only source records passing URL, identity, relevance,
  timing, supported-claim, duplicate, and contradiction gates.
- One NDJSON response emits a headline/summary block, consecutive section
  blocks, and a complete object. Each complete block is validated before
  persistence; the final report repeats full-envelope validation.
- Failure never replaces the previous valid report. The UI removes failed
  partial content and retains polling plus last-known-good fallbacks.

## Storage

| Migration | Active purpose | Applied state |
|---|---|---|
| 001 | Markets, outcomes, snapshots, metrics, signals, reports, related material, collection logs | Approved local development DB only |
| 002 | Context candidates and collection runs | Approved local development DB only |
| 003 | Versioned market resolution rules | Approved local development DB only |
| 004 | Immutable generation requests and append-only events/leases | Approved local development DB only |
| 005 | Individually validated generation blocks for SSE replay | Approved local development DB only |

Historical v1-v7 stored report/request rows were removed under explicit local
approval. Migrations, ADRs, compatibility code, and retained evidence reports
remain.

## Core invariants

- Aggregate market data only; no user account or wallet-level feature.
- Every data surface keeps data-as-of timing and interpretation caution.
- Missing history or evidence remains absent; values and sources are never
  fabricated.
- External material may provide attributed context but cannot be presented as
  the explanation for an observed movement.
- Authored factual sections require reconstructible evidence references.
- Source URLs, domains, titles, claims, levels, and parent links are checked at
  generation and read time.
- Prohibited-language validation runs before storage and again during public
  reconstruction where required.
- Production writes, deployments, schema changes, dependencies, infrastructure,
  and wording-policy changes retain human approval gates.

## Current implementation

- Frontend: shared Home/list/detail/methodology navigation; query-linked detail
  tabs; strict v8 parser; generation, streaming, failure, stale, and source
  states; responsive and accessibility checks.
- Backend: FastAPI issue and generation routes; SQLAlchemy models; scoped
  latest-row queries; static fallback; local worker launcher.
- Data: Gamma collector, CLOB historical seed, snapshot/metric calculations,
  fixed signal detection, source research/verification, v8 writer validation.
- Verification baseline: 488 Backend tests plus Frontend typecheck, lint, v8
  parser regression, and production build. The known bundle-size warning is
  tracked as TD-001.

## Open architecture work

- ISS-017 queued-request recovery after a lost worker.
- ISS-018 provider-compatible citation annotation handling.
- Future retention/downsampling for extended snapshot history.
