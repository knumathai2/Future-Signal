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

- **Role**: Frontend Implementer / Debugger
- **Branch**: `frontend/ISS-021-api-base-url`
- **Goal**: Make the configured Frontend API origin apply consistently to REST and SSE.
- **Status**: Completed

## Completed in ISS-021

- Added an origin-only `VITE_API_BASE_URL` utility shared by JSON, report,
  generation, polling, and SSE requests.
- Preserved relative `/api` paths when the setting is empty so local Vite proxy
  behavior remains unchanged.
- Rejected malformed bases, credentials, paths, queries, fragments, and
  protocol-relative API paths.
- Added a dedicated URL regression script and updated Frontend setup guidance.
- Documented but did not apply the hosting-environment, Backend CORS, Vercel,
  deployment, and production follow-up.
- Passed Frontend typecheck, lint, URL/parser scripts, configured/default
  production builds, Prettier and diff checks, plus actual Backend/Browser QA.

## Boundaries

- No user-facing copy, dependency, public API shape, schema, database, provider,
  infrastructure, deployment, or production state changed.
- The existing TD-001 bundle-size warning remains unchanged.

## Next handoff

Review and merge `frontend/ISS-021-api-base-url` through the project review flow.
TASK-122 remains in review on its existing branch.
