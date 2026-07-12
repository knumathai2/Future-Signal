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
| 006 | Ephemeral scenario sessions, turns, premises, requests, events, and validated response blocks | Unapplied |

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
  latest-row queries; static fallback; local worker launcher; default-off,
  local/development-only scenario session boundary.
- Data: Gamma collector, CLOB historical seed, snapshot/metric calculations,
  fixed signal detection, source research/verification, v8 writer validation.
- Verification baseline: 526 Backend tests plus Frontend typecheck, lint, v8
  parser regression, and production build. The known bundle-size warning is
  tracked as TD-001.

## Open architecture work

- ISS-017 queued-request recovery after a lost worker.
- ISS-018 provider-compatible citation annotation handling.
- Future retention/downsampling for extended snapshot history.
- Scenario writer/worker, shared rate limiting, scheduled expiry cleanup, and
  separate Frontend experience remain approval-gated follow-up work.

## Implemented default-off boundary — scenario conversation

TASK-124/125 define the Phase 2 policy and threat model. TASK-126 implements
only the API/storage boundary behind a disabled feature flag:

```text
anonymous browser + issue-scoped capability
  -> scoped API validation / limits / idempotency
  -> immutable turn request
  -> isolated tool-free worker
  -> typed issue facts + premise registry + bounded turns
  -> one provider call
  -> complete-block safety / leakage / Markdown validation
  -> ephemeral session storage
  -> authenticated fetch-SSE replay
```

The capability is 256-bit random material returned once; only its hash is
stored. A session is fixed to one issue, eight user turns, and a 24-hour
lifetime. The initial path has no model tools, live browser, user URL/file
ingestion, model-authored compaction, active links, or cross-device history.
Conversation content is append-only while live and is hard-deleted after expiry
or owner deletion. Existing issue/report/evidence history remains append-only
and untouched.

Migration 006 and matching ORM models now exist but the migration is unapplied.
The local/development-only API can create capability-scoped sessions, append
idempotent queued turns, read status, replay already validated stored blocks,
and hard-delete the ephemeral graph. It uses process-local keyed request
ceilings and exposes no capability in a URL or stored plaintext field.

No scenario worker, provider call, shared rate-limit infrastructure, scheduled
cleanup, Frontend tab, migration application, deployment, or production state
exists. The feature flag defaults off, and enabling it against a database
without migration 006 is unsupported.
