# TASK-106: On-demand v7 briefing UI

Date: 2026-07-11  
Owner: Frontend Implementer  
Branch: `frontend/TASK-106-on-demand-briefing-ui`  
Status: Complete

## Delivered behavior

- Replaced the v6-only runtime parser and report card with the strict v7
  flexible-section, source-level, cache, request, and last-good contract.
- Added an explicit `AI 브리핑 생성` action. The route appends or joins a
  request through the approved POST endpoint, polls the issue-scoped request,
  and reloads the public report after success or failure.
- Rendered idle, minimal/full generating, fresh, stale, failed, and
  failed-with-last-good states without blocking the issue, metrics, chart, or
  manually curated related-event area.
- Preserved the previous valid report during refresh and failure states and
  exposed refresh only when another request is meaningful.
- Rendered paragraph or bullet sections in server order. Public source cards
  show exact safe links, A-C source levels, retrieval time, and supported claim
  text; internal evidence excerpts remain out of the visible UI.
- Every report state retains a data-as-of timestamp and interpretation-caution
  notice. Legacy chart candidate types remain only until the separately
  approved TASK-109 cleanup.

## Verification

- Frontend typecheck, ESLint, v7 parser regressions, production build,
  Prettier, `git diff --check`, and the prohibited-wording scan pass.
- Browser QA covered fresh/no-source, A-level source, idle, generating, stale,
  and failed-with-last-good fixtures.
- At 1280px and 390px the document has no horizontal overflow; interactive
  buttons retain a minimum 44px height and the source link remains contained.
- No dependency, provider call, database write, migration application,
  infrastructure change, deployment, production action, or legacy deletion
  occurred.
