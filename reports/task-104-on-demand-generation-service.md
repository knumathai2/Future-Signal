# TASK-104: On-demand generation service and workflow separation

Date: 2026-07-11  
Owner: Backend / Data-AI  
Branch: `backend/TASK-104-on-demand-generation-service`  
Status: Complete

## Result

Normal market collection no longer generates any AI report. The separate v7
service owns request fingerprinting, duplicate joining, lease claim/recovery,
optional bounded context refresh, one-shot writing, deterministic validation,
append-only report storage, and outcome events.

## Cache and input bundle

The input bundle reconstructs the latest issue, metric/snapshot, resolution
definition, accepted non-expired v7 context, A-C sources, exact supported
claims, and deterministic limitation evidence. The SHA-256 fingerprint covers
all evidence plus prompt, policy, and input-schema versions.

Same-market/same-fingerprint requests join one identity. A failed identity can
receive a new queued event; evidence or version changes create a new identity.

## Worker behavior

- FIFO selection is bounded to 1-50 requests.
- A non-expired running lease cannot be claimed twice.
- An expired lease creates a later append-only running attempt.
- A context refresh that changes evidence creates a successor fingerprint
  request and closes the original with a safe supersession reason.
- Budget reservation occurs before the writer call.
- The writer is called exactly once; provider/schema/evidence/language/number
  failure appends a safe failure and preserves every prior successful report.
- Success stores a strict v7 envelope and appends an event linked to the exact
  report UUID.

## Context refresh

`refresh_v7_context_for_market()` builds broad research input, runs TASK-103
classification and conditional verification, and appends v7 candidate and run
audit records. Public candidates retain source level, exact excerpt-backed
claims, URL/domain/title/hash, research/verifier identity, expiry, and cost.

## Workflow separation

Normal scheduled collection ignores an accidentally supplied writer client.
Explicit guarded historical reports-only mode remains for TASK-108 comparison
and later TASK-109 review. The CLI now builds a writer client only for that
explicit mode. A standalone local/dev worker is available without adding a
queue dependency.

## Verification

- On-demand/service and scheduled-workflow focused suite: 23 tests.
- Full Backend suite: 428 tests passed.
- Ruff and `git diff --check` passed.
- No live provider call, non-test DB write, migration application, dependency,
  infrastructure, deployment, or production action occurred.
