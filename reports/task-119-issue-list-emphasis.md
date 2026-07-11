# TASK-119 — Full issue-list emphasis colors

_Date: 2026-07-12_  
_Branch: `frontend/TASK-119-issue-list-emphasis`_  
_Owner: Frontend Implementer_

## Outcome

The full issue list now uses the same restrained emphasis hierarchy as the
four-part detail screen:

- A terracotta marker anchors the page heading.
- Selected category, period, and sort filters use terracotta text/border on the
  soft accent surface.
- The result count and active pagination use terracotta emphasis.
- Each row shows the current reflected expectation value in terracotta and the
  selected-window observed change in muted blue.
- Row hover uses the soft accent surface while resting rows remain neutral.
- Search focus uses an accent border and soft ring.

Signs and labels continue to communicate direction. No green/red gain-loss
semantics were introduced.

## Verification

- `npm run typecheck`
- `npm run lint`
- `npm run test:report-parser`
- `npm run build`
- Prettier and `git diff --check`
- Actual local DB-backed desktop full-page Browser review: ten rows, selected
  filters, current/comparison values, pagination, no overflow.
- 320px Browser review: three visible selected filters at 44px, no page
  overflow, and zero console warnings/errors.

The pre-existing production bundle-size warning remains. No dependency, API,
schema, database, provider, infrastructure, deployment, production, wording-
policy, or legacy-runtime change occurred.
