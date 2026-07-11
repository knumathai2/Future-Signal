# TASK-118 — Four-part issue detail

_Date: 2026-07-11_  
_Branch: `frontend/TASK-118-issue-detail-tabs`_  
_Owner: Frontend Implementer_

## Outcome

The existing issue-detail route now uses four question-led tabs:

1. `개요` — issue identity, reflected expectation value, seven-day observed
   change, caution, data-as-of time, chart, and compact check items.
2. `AI 이슈 브리핑` — the complete existing v8 on-demand generation,
   validated-block, source, timing, stale, failure, and last-good surface.
3. `관련 자료` — dated candidate material alongside a fixed seven-day chart,
   plus accepted v8 sources with level, domain, retrieval time, supported
   claims, and exact safe links.
4. `해석 안내` — metric meaning, percent/percentage-point distinction,
   activity/liquidity, inflection markers, refresh timing, and limitations.

## Boundaries retained

- No public API or response shape changed.
- No candidate/source relationship is inferred from time proximity.
- Every metric-bearing tab keeps the issue data-as-of time and caution badge.
- AI generation remains user initiated and preserves streaming plus last-good.
- No new dependency, schema, database action, provider call, infrastructure,
  deployment, production action, wording-policy change, or legacy deletion.

## Navigation and responsive behavior

- The `tab` query parameter deep-links non-overview tabs and preserves other
  search parameters such as development report fixtures.
- Semantic tabs support ArrowLeft, ArrowRight, Home, and End.
- At 320px the tab rail scrolls horizontally while the page itself does not.
- A direct link scrolls the active tab into view.

## Visual emphasis follow-up

The user approved the first mockup's warm emphasis direction on 2026-07-12.

- Terracotta `#B84416` and soft `#FFF2E9` emphasize the active tab, current
  reflected expectation value, chart line/markers, timeline numbers, primary
  briefing action, and briefing summary edge.
- Muted blue `#466AA3` and soft `#EDF3FB` distinguish comparison values.
- Deep ink `#241C18` keeps headings warm and legible.
- Change direction remains encoded by sign and wording rather than green/red
  gain-loss styling.

## Verification

- `npm run typecheck`
- `npm run lint`
- `npm run test:report-parser`
- `npm run build`
- Prettier and `git diff --check`
- Contextual wording review: the only new contextual expression is the approved
  explicit limitation `보장하지 않습니다`; no hard-block expression was added.
- Actual local DB-backed Browser QA at 1280px, 390px, and 320px: all four tabs,
  URL state, keyboard movement, 44px controls, active-tab visibility, no page
  overflow, and zero clean-tab console warnings/errors.
- Post-color desktop and 320px Browser QA: exact rendered terracotta/blue token
  values, no page overflow, scrollable narrow tab rail, and zero console
  warnings/errors.

The production build retains the pre-existing bundle-size warning.
