<!--
Purpose:        Current implemented architecture and invariants
Owner:          Backend Implementer / Data-AI Implementer
Update Trigger: Implemented architecture or boundary change
Harness Version: 1.1
-->

# Architecture — Outlook Signals

_Last updated: 2026-07-13_

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
| 006 | Ephemeral scenario sessions, turns, premises, requests, events, and validated response blocks | Approved local development DB only |

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

- Frontend: shared Home/list/detail/methodology navigation; five query-linked
  detail tabs; strict v8 and scenario parsers; authenticated fetch-SSE,
  generation, failure, expiry, deletion, stale, and source states; responsive
  and accessibility checks.
- Backend: FastAPI issue and generation routes; SQLAlchemy models; scoped
  latest-row queries; static fallback; local worker launcher; default-off,
  local/development-only scenario session boundary.
- Deployment: Docker Compose keeps Backend unpublished on the internal `app`
  network while attaching a separate outbound-only `egress` network for the
  PostgreSQL connection; Frontend alone publishes `127.0.0.1:8600` via `edge`.
- Data: Gamma collector, CLOB historical seed, snapshot/metric calculations,
  fixed signal detection, source research/verification, v8 writer validation.
- Verification baseline: 526 Backend tests plus Frontend typecheck, lint, v8
  parser regression, and production build. The known bundle-size warning is
  tracked as TD-001.

## Open architecture work

- ISS-017 queued-request recovery after a lost worker.
- ISS-018 provider-compatible citation annotation handling.
- Future retention/downsampling for extended snapshot history.
- A successful scenario-writer evaluation, shared rate limiting, scheduled
  expiry cleanup, and production activation remain approval-gated follow-up work.

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

Migration 006 and matching ORM models now exist and the migration is applied
only to the approved local development DB.
The local/development-only API can create capability-scoped sessions, append
idempotent queued turns, read status, replay already validated stored blocks,
and hard-delete the ephemeral graph. It uses process-local keyed request
ceilings and exposes no capability in a URL or stored plaintext field.

TASK-128 adds a guarded local/development single-request writer. It serializes
only one issue's v8 evidence, server-owned premise classes, and bounded turns;
it provides no model tools and validates complete JSON, premise refs, wording,
leakage, numbers, restricted Markdown, and response blocks before storage. The
first two authorized evaluations cost USD 0.0117605 total and failed closed on
assumption framing and then ISO-date numeric normalization, leaving no assistant
turn or block. Both corrected detectors are tested, but a third call is not
authorized.

TASK-129 adds a fifth query-linked detail tab. The browser retains the raw
capability only in memory and sessionStorage, authenticates every read/write and
fetch-SSE replay without URL disclosure, validates exact response/block shapes,
renders only inert paragraph/list structures, polls after bounded stream
reconnect failure, preserves earlier turns on failure, and exposes expiry and
owner deletion states. The Frontend contains no provider client; a newly
created request may trigger only the guarded Backend child described below.

TASK-132 launches the existing guarded scenario worker as a detached child only
after a newly created local/development request commits. Idempotent replay does
not spawn a second child, and the API process still imports no provider client.
Its one approved response cost USD 0.0058895 and failed closed with
`unsupported_number`. No assistant turn or response block was stored. Writer
version 2 now parses allowed Markdown before number validation so ordered-list
indices are presentation metadata while numbers inside list items remain
evidence-gated.

TASK-133 consumed one separately approved writer-v2 call costing USD 0.006425.
It stored one validated assistant turn and three paragraph blocks. Authenticated
SSE completed, the Frontend rendered the response, and a reload reconstructed
the stored session with zero browser-console errors. This is the first
successful local scenario response; the server feature remains default-off.

TASK-134 bounds each PostgreSQL process to a default pool of three persistent
plus one overflow connection, instead of SQLAlchemy's effective 5+10 default.
Authenticated status reads and SSE may relaunch only attempt-zero requests that
remain queued for five seconds. A process-local 20-second cooldown and three-
launch cap prevent spawn storms, and `SELECT ... FOR UPDATE` serializes the
request claim before any provider work. Running or terminal attempts are never
automatically relaunched. The preserved queued request recovered after restart
with one USD 0.00634325 call and stored one assistant turn plus three blocks.

TASK-135 preserves complete response validation and append-only block storage,
then progressively replays those stored scenario blocks over authenticated SSE.
The first block is immediate and later blocks are paced at 0.2-second intervals.
Event payloads are materialized and the read transaction is released before
network pacing, so slow clients do not hold a database connection. Raw provider
fragments remain private and never cross the public API boundary.

No shared rate-limit infrastructure, scheduled cleanup, deployment, or
production state exists. The server feature flag defaults off.
