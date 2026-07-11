# TASK-110: Automatic on-demand worker launch

Date: 2026-07-11  
Branch: `backend/TASK-110-auto-worker-launch`

## Outcome

A queued `POST /api/issues/{id}/report/generate` now starts the existing v7
worker automatically in local/development. The API still only commits or joins
the request and returns HTTP 202; it does not import or construct a provider
client and does not wait for generation.

## Boundary

- The launcher invokes the current Python interpreter with
  `python -m app.core.on_demand_worker --request-id <uuid>`.
- The worker child owns the database lease, provider call, validation, report
  append, and terminal event append.
- Targeting the exact request avoids an older FIFO item consuming the one-shot
  process intended for the latest button click.
- Duplicate child launches remain safe because `claim_v7_request()` locks the
  immutable request row and accepts only one active lease.
- Spawn failure is logged without changing the HTTP 202 response or deleting
  the queued event, so the existing manual worker remains a recovery path.
- Auto-launch is limited to `local`, `dev`, and `development`; production
  worker deployment remains outside this task.

## Verification

- Launcher command, environment guard, detached-process settings, reaping, and
  spawn-failure behavior have focused unit coverage.
- API coverage proves a queued create/join invokes the request-scoped launcher.
- CLI coverage proves `--request-id` bypasses the FIFO queue scan.
- The full Backend suite passes 446 tests and Ruff lint.
- No provider call, non-test database write, deployment, infrastructure change,
  dependency change, schema change, or public response-shape change occurred.
