# TASK-108: Bounded development v6-v7 evaluation

Date: 2026-07-11  
Owner: Data/AI Implementer / Reviewer  
Branch: `data-ai/TASK-108-v7-development-evaluation`  
Status: Complete — v7 acceptance failed

## Guarded scope

- Environment: configured `ENV=local` development database.
- Applied existing append-only migration 004 to the development database only,
  under the approved TASK-099 schema/write boundary.
- Same two actual issues and same configured model used by the successful v6
  evaluation: Trump resignation and Israeli parliament dissolution.
- No context-research or verifier call was made. The existing metric,
  definition, and zero-public-source evidence was reused.
- No deployment, production write, new dependency, existing-migration edit, or
  legacy deletion occurred.

## Actual comparison

| Measure | v6 | v7 |
|---|---:|---:|
| Actual issues | 2 | 2 |
| Successful stored reports | 2 | 0 |
| Writer calls in final successful/reliability evaluation | 2 | 8 |
| Successful calls | 2 | 0 |
| Observed writer cost | USD 0.007316 | USD 0.077962 |
| Natural verified public sources | 0 | 0 |

The prior v6 rows produced strict no-evidence modes for both issues. V7 made
four bounded two-issue rounds while input-contract defects were corrected:

1. initial input: one unsupported-number and one blocked-word failure;
2. English month support and preferred status terms: two unsupported-number
   failures;
3. backend-owned percent/percentage-point display evidence: one blocked-word
   and one unsupported-number failure;
4. explicit 24-hour/7-day comparison-window evidence and stronger status-term
   guidance: one blocked-word and one unsupported-number failure.

Across all eight calls, six failed `unsupported_number` and two failed the
existing Korean blocked-word gate. Every attempt appended only request/event
audit rows; no invalid v7 report was stored and the API has no v7 last-good to
serve for these issues.

## Improvements retained

- English month names in cited definitions now support their ordinary Korean
  numeric-month representation without permitting unrelated numbers.
- Metric evidence now carries backend-owned percentage and percentage-point
  display values plus explicit 24-hour and 7-day comparison-window values.
- The positive prompt supplies preferred Korean status/evidence vocabulary and
  tells the writer to copy backend display units instead of calculating.
- Regressions cover each deterministic input improvement. Full Backend passes
  440 tests and Ruff.

## Acceptance decision

V7 is **not accepted for legacy cleanup**. Its evidence and failure boundaries
worked correctly, but the configured writer produced zero usable results for
the same two issues where v6 produced two. Flexible-section quality and UI
content cannot be judged from genuine v7 rows until reliability is improved.

TASK-109 may audit cleanup candidates, but v1-v6 runtime code must remain and
no deletion approval should be requested while this acceptance failure is
open as ISS-016.
