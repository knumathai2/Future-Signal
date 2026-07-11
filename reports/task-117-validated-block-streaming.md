# TASK-117: Validated-block briefing streaming

## Outcome

The v8 writer now supports one-call NDJSON generation and progressively exposes
only complete blocks that pass the active structure, evidence, source-parent,
URL, and wording validators. The final report still requires the full v8
validator and normal append-only `ai_reports` success event.

## Implementation

- Added append-only `005_ai_report_generation_blocks.sql` and its matching ORM
  model. The migration remained unapplied during implementation verification.
- Added strict headline/summary, section, and complete NDJSON models, arbitrary
  token-chunk buffering, consecutive-index and unique-section state, per-block
  validation, final validation, and a non-streaming compatibility path.
- Added provider streaming to the existing OpenAI-compatible client without a
  new dependency. Terminal request usage records first validated block, total
  writer milliseconds, and validated block count.
- Added issue-scoped SSE replay with active-attempt filtering,
  `Last-Event-ID`, keep-alives, terminal success/failure, and no raw text.
- Added strict Frontend stream parsing, progressive headline/section rendering,
  partial-state removal on failure, and existing polling fallback on transport
  failure. Data-as-of and interpretation caution stay visible.
- Added a localhost-only `report=v8-streaming` fixture for responsive visual
  verification.

## Verification

- Backend full suite: 488 passed.
- Focused Backend stream/schema/API suite: 61 passed.
- Ruff: changed Backend files clean.
- Frontend typecheck, ESLint, strict report/stream parser regression, and
  production build passed. The pre-existing bundle-size warning remains.
- Local Browser QA passed for the validated-block fixture at desktop and
  390×844. The report stayed within the viewport, retained data-as-of and
  caution context, exposed the live-region label, and produced no console
  warning or error.
- During implementation verification, no external provider call, database
  write, migration application, new dependency, infrastructure change,
  deployment, production action, or legacy deletion occurred. The separately
  approved local activation is recorded below.

## Approved local activation and latency sample

The user separately approved the currently configured `ENV=local` database and
one stored-evidence-only writer evaluation. Migration 005 was newly applied and
verified with six constraints and three indexes. No production database was
touched.

One actual OpenRouter generation for the Israeli-parliament issue succeeded on
attempt one with five authored sections and six stored validated blocks. Client
measurement from POST start was 9.700 seconds to the first headline/summary
block and 13.738 seconds to completion, allowing reading to begin about 4.038
seconds earlier. Worker-only measurement was 5.223 seconds to the first block
and 8.493 seconds total. Usage was 1,835 input tokens, 1,379 output tokens, and
USD 0.010567. The fresh v8 API response reconstructed successfully, and the
actual DB-backed Browser view showed all five sections, data-as-of, caution,
zero console warnings/errors, and the explicit no-public-source state.

No context research, second writer call, deployment, infrastructure change,
production write, new dependency, or legacy deletion occurred.
