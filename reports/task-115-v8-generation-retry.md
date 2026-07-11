# TASK-115 — V8 generation retry repair

Date: 2026-07-11  
Owner: Data/AI + Backend + Frontend  
Branch: `data-ai/TASK-115-v8-generation-retry`

## Diagnosis

The screenshot showed the static `ai-oversight-bill` fallback route. Chrome
logged `Failed to fetch` for detail, history, report, and generation requests
because the Frontend dev server was stopped. After restarting it, the Vite
proxy and Backend returned HTTP 200 and real chart history rendered normally.

AI generation had a second independent failure. The configured context path
could fail before writing when no standard citation annotations were returned.
A stored-evidence request reached the writer, but two outputs used the existing
blocked Korean expression `확정` and were rejected before storage.

## Repair

- Enumerated the existing Korean prohibited-expression list in the v8 system
  prompt without changing the filter.
- Preserved immutable request rows and fingerprints.
- Added a per-attempt append-only queued-event usage value so a failed request
  can be retried with `context_refresh_requested=false`.
- Initial requests still use their original context-refresh choice.
- Added a failed-state UI action, `저장된 근거로 다시 생성`, with explicit copy
  that the retry uses current stored evidence.

## Live verification

- Real issue: `17a54295-15aa-4d00-9854-ae42ab13bdc0`
- Real chart: rendered with seven-day history and the 5pp marker description
- Request: `8d7ed43c-87b2-491d-bbe8-e105d3714554`
- Attempts 1–2: failed closed on `banned_phrase:확정`
- Attempt 3: succeeded with report
  `d179b6fe-9873-41ac-95b6-2a7c17c17f33`
- Total observed writer cost: USD 0.02658845
- Public state: `fresh`, exact data-as-of and caution present, zero-source state
  shown honestly

## Verification

- Backend: 467 tests passed
- Ruff: full Backend clean
- Frontend: typecheck, ESLint, v8 parser regression, build, and Prettier passed
- Changed-copy prohibited-wording scan: passed
- Chrome: real chart and fresh v8 report verified together
- Known build warning: existing large bundle warning only

No schema, migration, dependency, infrastructure, deployment, production
write, or safety-policy relaxation occurred. ISS-018 remains open for actual
citation-backed source retrieval; this repair only prevents that failure from
permanently blocking a stored-evidence briefing.
