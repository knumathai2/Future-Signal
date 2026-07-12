# ISS-021 — Frontend API Base URL

_Date: 2026-07-12_

## Implemented Frontend boundary

- `VITE_API_BASE_URL` is optional and must be an absolute HTTP(S) origin.
- An empty value preserves the local Vite `/api` proxy flow.
- REST and SSE URLs use the same validated origin.
- URL paths must begin with exactly one slash.
- Credentials, paths, queries, and fragments are rejected in the configured
  origin to prevent accidental duplicated or ambiguous API paths.

## Infrastructure follow-up — not applied

A split-origin deployment still requires explicit human approval for all of
the following:

1. Set `VITE_API_BASE_URL` in the Frontend hosting environment to the approved
   Backend origin.
2. Add the deployed Frontend origin to the Backend CORS allowlist.
3. Confirm that CORS headers are present for normal REST responses, error
   responses, preflight requests, and the SSE stream endpoint.
4. Decide whether same-origin hosting should use a hosting rewrite instead of
   `VITE_API_BASE_URL`; do not configure both routing strategies implicitly.
5. Verify issue list/detail reads, report generation POST, request polling, and
   SSE replay from the deployed Frontend origin before release.

No hosting environment, Backend CORS setting, Vercel rewrite, deployment, or
production state was changed in ISS-021.
