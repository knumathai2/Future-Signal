# Review: TASK-012 Dashboard API Integration

Date: 2026-07-08  
Reviewer: Reviewer  
PR: #12 (`frontend/TASK-012-home-dashboard-ui` -> `main`)  
Verdict: Approved after reviewer fix

## Scope Reviewed

- Frontend API route integration in `frontend/src/App.tsx`
- Dashboard and detail rendering in `frontend/src/components`
- API response mapping and formatting in `frontend/src/utils/format.ts`
- Data-as-of timestamp and interpretation-caution placement
- Project wording policy for changed frontend strings
- GitHub merge state against latest `origin/main`

## Finding Fixed

### P1: Missing reference data was displayed as `0.0pp`

`change_24h` and `change_7d` can be `null` in the accepted API contract when
the backend lacks enough reference data. The PR mapped those values to `0`,
which made "insufficient data" look like "no observed change." That conflicts
with PRD §8.5 and the Day 2 data rule that missing references must never be
fabricated.

Fix applied:

- Preserved nullable change metrics in the frontend `Issue` type.
- Updated API mapping to keep null values instead of converting them to zero.
- Updated percentage-point formatting to render `insufficient data`.
- Updated dashboard weekly sorting to place missing weekly change values after
  available values.
- Updated detail summaries to explain when a selected window lacks enough
  reference data.

## Merge State

PR #12 was `DIRTY` against `main` because `memory/session.md` conflicted with
the latest main branch. The conflict was documentation-only and was resolved on
the review branch while preserving the latest TASK-007 mainline artifacts.

## Verification

- `npm ci` -> passed using the existing frontend lockfile
- `npm run typecheck` -> passed
- `npm run lint` -> passed
- `npm run build` -> passed with the existing Recharts chunk-size warning
- Content wording scan over `frontend/src` -> no prohibited or use-carefully
  wording hits after word-boundary filtering
- `git diff --check` -> passed before merge-conflict resolution

## Notes

- No dependency, schema, public API, infrastructure, deployment, production DB,
  or paid external API change was made.
- The npm install surfaced existing audit warnings; dependency upgrades were
  intentionally not performed because that requires separate scope and approval.
