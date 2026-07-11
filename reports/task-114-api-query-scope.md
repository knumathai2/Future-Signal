# TASK-114 — API query scope repair

Date: 2026-07-11  
Owner: Backend Implementer  
Branch: `backend/TASK-114-api-query-scope`

## Outcome

ISS-017's accumulated-history read bottleneck is removed without changing the
public API contract, database schema, dependencies, infrastructure, deployment,
or non-test database state. Orphaned queued-request recovery remains a separate
open part of ISS-017.

## Endpoint query changes

| Endpoint | Previous read path | Current read path |
|---|---|---|
| `GET /api/issues/{issue_id}/report/requests/{request_id}` | Rebuilt every live issue from all snapshots and metrics before reading one request | Parses the issue UUID, reads one request by primary key, compares `market_id`, then reads the latest event with ordered `LIMIT 1`; snapshot and metric tables are not queried |
| `POST /api/issues/{issue_id}/report/generate` | Rebuilt every live issue before reconstructing the requested issue's evidence | Reads the market primary key and reconstructs only that market's latest metric, snapshot, definition, and accepted context before preserving the existing fingerprint/join/queue behavior |
| `GET /api/issues/{issue_id}/report` | Rebuilt every live issue before reading reports and evidence | Reads the requested market, up to 20 recent v8 rows, its latest request, and only market-scoped latest metric/snapshot/definition/context evidence; strict previous-valid fallback remains |
| `GET /api/issues/{issue_id}` | Reduced all snapshot and metric history in Python | `load_live_issue()` reads the market, tracked outcome, latest snapshot, and latest metric with market predicates and ordered `LIMIT 1`; related events and signals remain market-scoped |
| `GET /api/issues/{issue_id}/history` | Rebuilt all live issues, then queried a lower-bounded interval | Uses the single-issue boundary for serviceability/data-as-of, then queries only the requested market with both lower and upper window bounds |
| `GET /api/issues` | Loaded all snapshot and metric rows and selected first-per-market in Python | Portable `row_number()` subqueries select only the latest snapshot, metric, and tracked outcome per market; heat/change/recent sort and pagination run in SQL when derived category classification is not required |
| `GET /api/categories` | Shared the accumulated-history loader | Reads only current servable issue rows from the same latest-per-market SQL boundary, then applies the existing broad Korean taxonomy |

## Preserved behavior

- Existing request and response fields and HTTP status meanings
- Static fallback and honest `data_as_of`
- Incomplete-data exclusion and insufficient-metric handling
- Fresh, stale, generating, failed, failed-with-last-good, and idle report states
- Strict v8 evidence reconstruction and previous-valid fallback
- Append-only request/event behavior and worker-launch meaning

## Verification

- Priority regressions: 80 issue/report API tests passed
- Full Backend: 466 tests passed
- Ruff: full Backend clean
- Public API/OpenAPI: 11 focused regressions passed
- Frontend: typecheck, lint, v8 parser regression, and production build passed
- SQL observation tests verify request-status table isolation, ID-route market
  predicates and limits, history market/time bounds, and list/category window
  functions
- `git diff --check`: clean before completion recording

The Frontend build retains the known bundle-size warning. No user-facing string
changed, so no new wording-lint surface was introduced.

## Remaining risk

The optimized query shapes are covered on SQLite and use SQLAlchemy window
functions supported by PostgreSQL, but this task did not run an `EXPLAIN` on
the development database because no external database action was needed. If
production-scale latency remains high, an index proposal must be measured and
approved separately before any schema change.

ISS-017 remains open because a queued request can still be orphaned after a
failed/missing worker launch or process restart. This task intentionally does
not mutate request state or add startup/polling recovery.
