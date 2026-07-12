<!--
Purpose:        Current session handoff only
Owner:          Currently active agent
Update Trigger: Every session
Harness Version: 1.1
-->

# Current Session — Outlook Signals

_Last updated: 2026-07-12_

Git history preserves earlier session states; do not create per-session archive
files.

## Session

- **Role**: Backend Implementer
- **Branch**: `backend/TASK-126-scenario-conversation-boundary`
- **Goal**: Implement the approved default-off scenario API/storage boundary.
- **Status**: Completed

## Completed in TASK-126

- Added unapplied append-only migration 006 and matching constrained ORM models.
- Added a disabled-by-default, local/development-only scenario API with a
  one-time capability, stored hash authentication, strict issue/session scope,
  idempotent turn enqueueing, status reads, and authenticated fetch-SSE replay.
- Enforced 24-hour fixed expiry, eight user turns, one active request, message
  and cumulative text bounds, current-input fingerprint stability, and
  process-local keyed request ceilings.
- Added explicit owner/expiry hard deletion for only the ephemeral graph.
- Passed 24 focused tests, all 526 Backend tests, and Ruff.

## Boundaries

- Migration 006 was not applied to any database and the feature defaults off.
- No scenario provider client, writer, worker, shared rate-limit store,
  scheduled cleanup, Frontend, new dependency, infrastructure, deployment, or
  production state was added or changed.
- Active v8 and historical reconstruction remain unchanged.

## Next handoff

TASK-127 may define the deterministic premise-state builder within the accepted
policy. Migration application, provider/writer evaluation, shared abuse and
cleanup infrastructure, Frontend, deployment, and production remain later
approval gates.
