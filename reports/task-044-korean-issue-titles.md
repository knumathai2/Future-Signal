# TASK-044: Korean Issue Display Titles

Date: 2026-07-09
Branch: `frontend/TASK-044-korean-issue-titles`
Owner: Frontend Implementer

## Scope

The dashboard previously rendered raw Polymarket market titles as primary issue
headlines. Many were English question strings, so users could not quickly tell
what real-world issue a card represented.

## Implementation

- Added optional frontend issue display fields:
  - `sourceTitle`
  - `displaySubtitle`
  - `topicLabel`
  - `resolutionCondition`
- Added `frontend/src/utils/issueDisplay.ts` to map the current live/demo issue
  set to Korean display copy:
  - topic label
  - short issue display title
  - one-line 기준 조건
  - detail-screen source title provenance
- Updated API-to-frontend mapping so the public API remains unchanged.
- Updated dashboard cards and weekly rows to show Korean topic/title/subtitle
  instead of raw English market titles.
- Updated detail headers to show Korean display title and 기준 조건 first, while
  keeping the original market question as small provenance text.
- Updated static fallback/dummy issue construction to populate display subtitle
  fields from existing Korean descriptions.

## Verification

- `cd frontend && npm run typecheck` — passed.
- `cd frontend && npm run lint` — passed.
- `cd frontend && npm run build` — passed with the existing Recharts chunk-size warning.
- Browser smoke at `http://127.0.0.1:5173/`:
  - Dashboard cards show Korean issue titles such as `가자 휴전 조건 이슈`.
  - Cards show one-line 기준 조건 subtitles.
  - Detail header shows Korean title, 기준 조건, and original market question
    only as secondary provenance.
- Changed-string safety scan passed; only code-level false positives such as
  `short` in formatter names remained.
- `git diff --check` — passed.

## Notes

No backend API shape, database schema, dependency, infrastructure, deployment,
or database write changed.
