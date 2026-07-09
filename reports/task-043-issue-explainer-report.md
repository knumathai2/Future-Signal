# TASK-043: Issue Explainer Report Output

Date: 2026-07-09  
Branch: `data-ai/TASK-043-issue-explainer-report`  
Owner: Data/AI Implementer

## Scope

User approved changing the public `/api/issues/{id}/report` content shape from
the original numeric 5-section summary to an 8-section issue explainer:

- `issue_explainer`
- `why_it_matters`
- `current_reading`
- `scenario_major_change`
- `scenario_limited_change`
- `scenario_status_quo`
- `check_points`
- `caution_note`

The scenario sections intentionally avoid value labels such as best/worst and
describe only conditional meanings of the market question.

## Implementation Notes

- Advanced `PROMPT_VERSION` to `v2`.
- Updated the fixed system prompt to generate plain-language Korean issue
  explainers for general readers.
- Kept strict JSON parsing with `extra="forbid"` and the existing
  banned-phrase/pattern safety filter before storage.
- Updated FastAPI and frontend report schemas to the new fields.
- Updated the report card labels to show issue meaning, importance, current
  reading, three conditional scenario sections, checkpoints, and caution.
- Added live API defense for legacy stored v1 report content: if the latest
  successful row does not validate against the current schema, the route returns
  `{"status": "not_yet_generated"}` instead of serving partial or mismatched
  content.
- Updated `backend/API_CONTRACT.md`, Technical Design §10, ADR-028, architecture,
  and project state notes.

## Verification

- `cd backend && .venv/bin/ruff check app tests` — passed.
- `cd backend && DATABASE_URL= .venv/bin/pytest tests/test_ai_report_batch.py tests/test_scheduled_batch.py tests/test_issues_live.py` — 42 passed.
- `cd backend && DATABASE_URL= .venv/bin/pytest` — 130 passed.
- `cd frontend && npm run typecheck` — passed.
- `cd frontend && npm run lint` — passed.
- `cd frontend && npm run build` — passed with the existing Recharts chunk-size warning.
- `git diff --check` — passed.
- Changed-string safety scans found only the documented prohibited-word list in
  prompts/docs and removed legacy sample lines; no new Korean hard-block terms
  were found in changed UI/prompt content.

## Remaining Operational Note

The configured development DB may still contain successful v1 `ai_reports`
rows. Those are now treated as `not_yet_generated` until a separately approved
reports-only batch writes v2 summaries. The regeneration selector treats a
successful report with a legacy `prompt_version` as eligible for v2 generation,
even when that legacy report is not yet stale.
