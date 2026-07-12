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

- **Role**: Debugger / Backend / Frontend
- **Branch**: `debug/ISS-020-url-hardening`
- **Goal**: Correct public-source, canonical, route-state, and API-path URL errors.
- **Status**: Completed

## Completed in ISS-020

- Added one shared Backend public HTTP(S) URL parser that rejects credentials,
  localhost, single-label/numeric browser aliases, and non-global IP targets.
- Preserved IPv6 brackets during canonicalization and applied the public URL
  boundary to context, v7, and resolution-source response schemas.
- Preserved the exact stored source URL after Frontend validation.
- Normalized invalid detail-tab query values and consistently encoded report
  path IDs.
- Passed 502 Backend tests, Ruff, Frontend typecheck/lint/parser tests,
  production build, Prettier checks, diff checks, and Browser verification.

## Boundaries

- No user-facing copy, dependency, public API shape, schema, database, provider,
  infrastructure, deployment, or production state changed.
- The existing TD-001 bundle-size warning remains unchanged.

## Next handoff

Review and merge `debug/ISS-020-url-hardening` through the project review flow.
TASK-122 remains in review on its existing branch.
