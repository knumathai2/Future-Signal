<!--
Purpose:        Implemented architecture and invariants
Owner:          Backend / Data-AI maintainers
Update Trigger: Runtime boundary, schema, API, or deployment change
Harness Version: 1.1
-->

# Architecture — Outlook AI Signals

_Last updated: 2026-07-13_

## System overview

```text
Polymarket Gamma/CLOB
        |
        v
market-data collector
  normalize -> snapshots -> metrics -> signals -> collection log
        |
        v
PostgreSQL <-> FastAPI <-> React/Vite
        ^          |
        |          +---- briefing generation request
        |          |
        |          +---- capability-scoped scenario request
        |                       |
        +---- isolated request workers
                evidence/context -> validated blocks -> final state
                                      |
                                      v
                              SSE replay / polling
```

## Runtime boundaries

### Market collection

- `.github/workflows/four-hour-collection.yml` runs at minute 17 every four
  UTC hours and supports manual dispatch.
- Scheduled collection receives database configuration only and explicitly skips
  context research and briefing generation.
- Gamma records are normalized to active binary issues. Invalid records are
  quarantined without stopping the batch.
- Snapshots, metrics, signals, and collection logs are append-only.
- The guarded CLOB history seed is restricted to local/development use and never
  rewrites existing snapshots.

### Public API

- Issue, category, and history reads are market- and time-bounded.
- Read failures degrade to timestamped static issue data and honest empty report
  or source states.
- Briefing and scenario writes append immutable request/event state.
- The API process never constructs a provider client.
- Request status and SSE endpoints expose only safe state and already validated
  blocks.

### Briefing worker

- A request-scoped worker claims queued or expired-running requests with bounded
  leases.
- Input fingerprints cover prompt, policy, schema, definition, metric, snapshot,
  context, and source evidence.
- Optional context refresh accepts only sources passing URL, identity, relevance,
  timing, supported-claim, duplicate, and contradiction gates.
- One NDJSON response contains a headline/summary block, consecutive section
  blocks, and a complete object. Each complete block is validated before
  persistence; the final report repeats full-envelope validation.
- Failure removes partial output and retains the previous valid report.

### Scenario worker

- A random 256-bit bearer capability owns one issue-scoped anonymous session;
  only its hash is stored.
- Sessions last 24 hours, allow at most eight user turns, and store no capability,
  IP address, user agent, or browser history.
- The worker receives one issue's stored evidence, server-owned premise classes,
  and bounded turns. It has no browser, external tools, user URLs, or file input.
- Complete output must pass premise-reference, evidence, wording, leakage,
  numeric, restricted-Markdown, length, and schema validation before storage.
- Authenticated fetch-SSE replays stored paragraph/list blocks. Raw provider
  fragments never cross the public boundary.
- Owner deletion or expiry removes only the ephemeral conversation graph.

## Storage

| Migration | Purpose                                                                                        |
| --------- | ---------------------------------------------------------------------------------------------- |
| 001       | Markets, outcomes, snapshots, metrics, signals, reports, related material, and collection logs |
| 002       | Context candidates and collection runs                                                         |
| 003       | Versioned market resolution rules                                                              |
| 004       | Immutable briefing generation requests, events, and leases                                     |
| 005       | Individually validated briefing blocks for SSE replay                                          |
| 006       | Ephemeral scenario sessions, turns, premises, requests, events, and response blocks            |

Existing migrations are immutable. New schema work must use a new append-only
migration and follow the approval rules in `AGENTS.md`.

## Request recovery and resource bounds

- Each PostgreSQL process defaults to three persistent connections plus one
  overflow connection.
- Briefing workers recover expired-running leases; a queued request may also be
  processed manually by exact request ID.
- Scenario status/SSE reads may relaunch only attempt-zero requests that have
  remained queued for at least five seconds.
- Scenario relaunch uses a process-local 20-second cooldown, a three-launch cap,
  and row locking before a request becomes `running`.
- Running and terminal scenario attempts are never automatically retried.

## Public category boundary

Stored source categories remain unchanged. The public API derives and publishes
only `정치`, `경제`, `환경`, `기술`, and `세계` when they contain servable
issues. Sports and catch-all labels do not appear in navigation. Stablecoin,
Tether, USDC, and USDT topics map to `경제` before the catch-all is considered.

## Deployment

- `deploy/compose.yml` runs the Backend and built Frontend on isolated Docker
  networks.
- Only the Frontend gateway is bound to `127.0.0.1:8600`; Caddy terminates TLS
  for the configured public host.
- The Backend uses an internal application network plus a separate outbound
  network for PostgreSQL and provider access.
- The checked-in production profile explicitly enables generation workers and
  scenario conversations. Both flags default to disabled in application code.
- Credentials remain outside the repository in ignored environment files.

## Core invariants

- Aggregate market data only; no account or wallet-level feature.
- Every data surface includes data timing and interpretation caution.
- Missing history or evidence is never fabricated.
- External context is attributed and never presented as the explanation for an
  observed movement.
- Authored factual content requires reconstructible evidence references.
- Unsafe URLs, unsupported claims, unknown references, and prohibited wording
  block storage or public reconstruction.
- Provider failure never replaces the previous valid result.
- Production writes, deployments, schema changes, dependencies, infrastructure,
  and wording-policy changes require explicit approval.
