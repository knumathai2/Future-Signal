# TASK-105: V7 generation, status, cache, and report API

Date: 2026-07-11  
Owner: Backend Implementer  
Branch: `backend/TASK-105-on-demand-report-api`  
Status: Complete

## Public operations

- `POST /api/issues/{id}/report/generate` validates the live issue/evidence
  bundle and creates or joins one fingerprint request. It returns HTTP 202 and
  performs no provider call.
- `GET /api/issues/{id}/report/requests/{request_id}` returns the latest
  append-only queued/running/succeeded/failed event, attempt, times,
  fingerprint, report/error, and successor request.
- `GET /api/issues/{id}/report` returns idle, minimal generating/failed, or a
  full strict v7 report in fresh/stale/generating/failed-with-last-good state.

## Strict v7 read reconstruction

Each candidate report is rebuilt against its generation-time metric/snapshot,
exact definition revision, ordered context IDs, accepted A-C sources, supported
claims, source URL/domain, evidence snapshot, fingerprint, deterministic
limitations/caution, language/ref/number gates, and timestamps.

The latest malformed or mismatched row is skipped. Only a previous valid v7
row may become last-good. V1-v6 are audit-only. A current fingerprint mismatch
marks the report stale; queued/running refresh and failed refresh states retain
the readable last-good report.

## API safety

- Request IDs are scoped to their issue.
- POST bodies reject extra fields.
- Static fallback cannot generate or fabricate a report.
- The API writes only immutable request and queued-event rows and never calls a
  research or writer provider.
- CORS permits GET and the approved POST only.

## Verification

- Added v7 API coverage for idle, duplicate join, queue polling, successful
  fresh report, stale fingerprint, failed-with-last-good, malformed newest
  fallback, exact A-level source/claim/link, issue scoping, body validation,
  and OpenAPI schemas.
- Historical v1-v6 tests now prove those rows are audit-only under v7.
- Full Backend suite passes 437 tests; Ruff and diff checks pass.
- No live provider call, non-test DB write, migration application, dependency,
  infrastructure, deployment, or production action occurred.
