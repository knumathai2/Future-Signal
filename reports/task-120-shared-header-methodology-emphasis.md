# TASK-120 — Shared header and methodology emphasis

_Date: 2026-07-12_  
_Branch: `frontend/TASK-120-shared-header-methodology-emphasis`_  
_Owner: Frontend Implementer_

## Outcome

### Home navigation

- Desktop primary navigation now lives in the same right-aligned shared-header
  group used across issue routes.
- The optional refresh action follows the navigation in that group, so it no
  longer causes the home navigation to appear centered.
- Mobile retains the shared three-column navigation row.

### Methodology emphasis

- Added the shared terracotta heading marker and eyebrow.
- Changed the return link to a 44px soft-accent outlined action.
- Replaced the long divided container with five numbered neutral guidance
  cards: two columns on desktop and one column on mobile.
- Card bodies remain neutral; accent is limited to numbers, heading context,
  action border, and hover border.

## Verification

- `npm run typecheck`
- `npm run lint`
- `npm run test:report-parser`
- `npm run build`
- Prettier and `git diff --check`
- Actual local desktop Browser review of home header and full methodology.
- 320px Browser QA: shared navigation, five 288px cards, 44px return action,
  no horizontal overflow, and zero console warnings/errors on both routes.

The pre-existing production bundle-size warning remains. No dependency, API,
schema, database, provider, infrastructure, deployment, production, wording-
policy, or legacy-runtime change occurred.
