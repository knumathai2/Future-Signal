<!--
Purpose:        TASK-126 implementation and verification record
Owner:          Backend Implementer
Update Trigger: TASK-126 scope or evidence correction
Harness Version: 1.1
-->

# TASK-126 — Scenario Conversation Boundary

_Completed: 2026-07-12_

## Outcome

Implemented the approved storage and HTTP boundary for an ephemeral,
issue-scoped scenario conversation. The feature is disabled by default and can
run only in `local` or `development`. It queues work but neither constructs a
provider client nor starts a scenario worker.

## Delivered

- Added append-only migration `006_scenario_conversations.sql` without applying
  it to a database.
- Added constrained session, turn, premise, generation-request, event, and
  validated-response-block models with same-session composite references.
- Added session creation with a one-time random 256-bit capability; persistence
  contains only its SHA-256 hash.
- Added non-enumerating bearer authentication for session reads, turn creation,
  status, authenticated fetch-SSE replay, and owner deletion.
- Added UUID idempotency, one active request, eight user turns, 1,000-character
  input, 2,500-character assistant blocks, 20,000-character session total, and
  fixed 24-hour expiry checks.
- Bound each session to the current v8 input fingerprint so changed issue input
  fails closed rather than mixing incompatible context.
- Added process-local keyed request ceilings without retaining a raw address.
- Added explicit expiry/owner hard deletion of the scenario graph while leaving
  the parent market and existing reports/evidence untouched.
- Added `no-store`, no-referrer, and authorization-varying response headers.

## Security properties verified

- A missing, malformed, incorrect, or cross-session capability cannot read or
  mutate conversation state.
- A capability never appears in an endpoint path, persisted plaintext field, or
  SSE cursor.
- Cross-session premise and assistant-turn references fail database constraints.
- Streaming exposes only complete persisted response blocks and supports replay
  from `Last-Event-ID`.
- Expired sessions reject access and can be hard-deleted by the cleanup helper.
- Deleting a scenario session does not delete its public issue.
- The API is unavailable when the flag is off or the environment is not local
  or development.

## Verification

```text
DATABASE_URL= .venv/bin/pytest -q tests/test_scenario_models.py tests/test_scenario_api.py
24 passed

.venv/bin/ruff check .
All checks passed!

DATABASE_URL= .venv/bin/pytest -q
526 passed
```

## Unchanged approval gates

- Migration 006 application to any database.
- Scenario writer, worker launch, provider call, or paid evaluation.
- New dependency, shared/multi-instance rate limiting, or scheduled cleanup.
- Frontend scenario experience.
- Infrastructure, deployment, production database, or production activation.
- Active v8 summary/runtime transition.
