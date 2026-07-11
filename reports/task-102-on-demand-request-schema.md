# TASK-102: Append-only generation request, lease, and recovery schema

Date: 2026-07-11  
Owner: Backend Implementer  
Branch: `backend/TASK-102-on-demand-request-schema`  
Status: Complete

## Result

Added append-only migration `004_ai_report_generation_requests.sql` and matching
SQLAlchemy models for an immutable request identity plus append-only lifecycle
events.

## Request identity

`ai_report_generation_requests` stores:

- UUID request and market IDs;
- unique `(market_id, input_fingerprint)`;
- exact prompt, policy, and input-schema versions;
- `user` or `development_evaluation` origin;
- bounded context-refresh intent;
- exact input evidence references; and
- request time.

The fingerprint is lowercase SHA-256 hex. It must cover issue ID, latest metric,
market-definition revision, accepted-context revision, prompt version, policy
version, and input-schema version. Repeated clicks join the same immutable row.

## Append-only events

`ai_report_generation_events` records:

- `queued` with no lease or outcome;
- `running` with attempt number, lease UUID, and expiry;
- `succeeded` with the exact append-only report UUID; or
- `failed` with a secret-free error code.

Database checks reject missing or mixed state fields. Usage is an aggregate
JSON object and cannot contain provider keys, prompts, or responses.

## Claim and recovery algorithm

1. Lock the request identity with `SELECT ... FOR UPDATE`.
2. Load its latest event ordered by `(recorded_at DESC, id DESC)`.
3. Join an existing queued/running request for the same fingerprint.
4. Do not claim a non-expired running lease.
5. If queued or expired, append a new running event with the next attempt and a
   bounded lease.
6. Generate outside the claim transaction.
7. Lock again, verify the lease token is still the latest running event, then
   append exactly one success or safe failure event.
8. A crashed worker leaves an expiring event; a later worker appends a new
   attempt without rewriting history.

## Verification

- Ten SQLite/Postgres-contract tests pass: allowed histories, fingerprint
  idempotency, invalid state shapes, report FK, cascades, JSONB/timestamptz,
  indexes, and additive migration checks.
- Ruff and `git diff --check` pass.
- Migrations 001-003 were not edited.
- Migration 004 was not applied to any database in this task.

No provider, database, API, workflow, dependency, infrastructure, deployment,
or production action occurred.
