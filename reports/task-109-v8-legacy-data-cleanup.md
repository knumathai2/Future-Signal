# TASK-109: V8 legacy stored-report cleanup

Date: 2026-07-12  
Owner: Reviewer / Backend  
Branch: `review/TASK-109-v8-legacy-data-cleanup`  
Status: Stored-data cleanup complete; legacy runtime-code cleanup remains separate

## Approved boundary

After reviewing the configured database with read-only queries, the user
explicitly approved deletion of old AI-report data. The executed boundary was
limited to the configured `ENV=local` development database:

- delete `ai_reports` rows with prompt versions v1 through v7;
- delete v7 generation requests and their cascading events/blocks;
- preserve every v8 report, request, event, validated block, metric, snapshot,
  source candidate, resolution rule, market row, and migration;
- make no provider call, schema change, deployment, infrastructure change, or
  production write.

## Execution result

The cleanup ran in one database transaction after an explicit `ENV=local`
guard.

| Record | Before | Deleted | After |
|---|---:|---:|---:|
| v1-v7 `ai_reports` | 241 | 241 | 0 |
| v7 generation requests | 10 | 10 | 0 |
| events owned by v7 requests | 38 | 38 by FK cascade | 0 |
| blocks owned by v7 requests | 0 | 0 | 0 |
| v8 `ai_reports` | 6 | 0 | 6 |
| v8 generation requests | 11 | 0 | 11 |
| v8 generation events | 60 | 0 | 60 |
| v8 validated blocks | 17 | 0 | 17 |

## Verification

- No v1-v7 report or v7 request remains.
- No orphan generation event or block exists.
- No succeeded event has a null report reference.
- FastAPI `GET /api/health` returned 200 through `TestClient`.
- Four markets with stored v8 reports returned 200 in fresh, stale, and
  failed-with-last-good states, confirming v8 evidence reconstruction and
  fallback remained intact.

This action removes stored legacy report history only. Historical contracts,
ADRs, tests, migrations, and v1-v7 compatibility/runtime code were not deleted.
