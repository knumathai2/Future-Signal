# TASK-085 Evidence-scaled Scenarios

Date: 2026-07-11
Owner: Data/AI Implementer
Status: Complete

## Result

- Added deterministic input completeness levels to the v5 writer payload.
- Changed scenario arrays from three-to-four items to one-to-four across writer,
  public API schema, Frontend runtime parser, and TypeScript behavior.
- Enforced completeness-specific scenario counts:
  - complete definition: one to four;
  - partial definition: one to three;
  - missing definition with verified context: one or two;
  - missing definition without verified context: exactly one limitation item.
- Updated the prompt to prohibit procedural paths when definition evidence is
  absent.
- Added backend and frontend regressions for a one-scenario valid report and
  overfilled missing-definition rejection.

No external model call or database write was performed.

## Verification

- Backend report/API tests: 188 passed.
- Ruff: clean after import normalization.
- Frontend typecheck: passed.
- Frontend v5 runtime parser regression: passed.
