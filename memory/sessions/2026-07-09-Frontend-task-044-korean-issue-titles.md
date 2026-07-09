<!--
Purpose:        Current session state - context handoff among agents
Owner:          Currently active agent
Update Trigger: Read at session start; must update before session ends
Harness Version: 1.1
-->

# Current Session - Outlook Signals

> After this session, copy this file to `memory/sessions/YYYY-MM-DD-[ROLE].md`.

---

## Session Info

- **Date**: 2026-07-09
- **Agent Role**: Data/AI Implementer
- **Session Goal**: Complete `TASK-043` AI report output structure update to issue-explainer scenarios.
- **Branch**: `data-ai/TASK-043-issue-explainer-report`

## Previous Session Summary

PM created the `TASK-041` implementation task from latest `origin/main` and
recorded `ISS-005`: historical seed records metric timestamps one microsecond
after the latest snapshot, while the report prompt-input lookup required exact
timestamp equality.

## Current Work

- [x] Fetched `origin/main` and created branch
      `data-ai/TASK-041-report-generation-readiness` from `01df91b`.
- [x] Updated `backend/app/core/ai_report_batch.py` so
      `build_prompt_inputs_for_market()` selects the latest snapshot with
      `captured_at <= market_metrics.computed_at`, instead of requiring exact
      timestamp equality.
- [x] Preserved the no-fabrication behavior: if there is no snapshot at or
      before the metric timestamp, prompt input construction returns `None` and
      the batch skips that market.
- [x] Added tests in `backend/tests/test_ai_report_batch.py` for the
      historical-seed `+1 microsecond` timestamp case, future-only snapshot
      rejection, and full `run_ai_report_batch()` insertion of a
      `status=success` row with a fake `LLMClient`.
- [x] Added local/demo run notes in
      `reports/task-041-report-generation-readiness.md`, including the expected
      `not_yet_generated` empty state before approval and the approved-only
      procedure for creating stored summaries.
- [x] Updated `tasks/active.md`, `tasks/completed.md`,
      `memory/known-issues.md`, `memory/architecture.md`,
      `memory/project.md`, and `reports/day-4-work-allocation.md` for closeout.

## Files Changed

- `backend/app/core/ai_report_batch.py`
- `backend/tests/test_ai_report_batch.py`
- `reports/task-041-report-generation-readiness.md`
- `reports/day-4-work-allocation.md`
- `tasks/active.md`
- `tasks/completed.md`
- `memory/known-issues.md`
- `memory/architecture.md`
- `memory/project.md`
- `memory/session.md`
- `memory/sessions/2026-07-09-DataAI-task-041-report-readiness.md`

## Verification

- [x] `cd backend && ruff check .` — passed.
- [x] `cd backend && pytest tests/test_ai_report_batch.py` — 17 passed.
- [x] `cd backend && pytest` — attempted; failed only because this local
      environment loaded a configured DB URL and the Python 3.13 environment
      lacks `psycopg2`, causing 7 `tests/test_issues_contract.py` failures
      during DB engine initialization.
- [x] `cd backend && DATABASE_URL= pytest` — 117 passed through the intended
      DB-free fallback test path.

## Notes / Remaining Risks

- No `.env` contents were printed or modified.
- No schema changes, dependency changes, infrastructure changes, deployment,
  public API shape changes, real OpenAI calls, or shared/dev database writes
  were performed.
- `ISS-005` is resolved as a code-readiness bug. The configured development DB
  may still have no successful `ai_reports` rows until the user separately
  approves the database write run. The user later clarified that the provided
  `OPENAI_API_KEY` may be used without separate per-run approval for
  project-scoped OpenAI report generation.
- PM still owns `TASK-040` and `TASK-018`.

## Follow-up Review: Approval-Gated Side Effects

- **Date**: 2026-07-09
- **Agent Role**: Reviewer
- **Scope**: Confirm whether `TASK-041` introduced or performed OpenAI calls,
  local/dev/shared DB writes, schema changes, dependency changes, or public API
  shape changes.
- **Result**:
  - No real OpenAI call was performed.
  - No shared/dev DB write was performed; new write assertions run only against
    the test suite's in-memory SQLite database with a fake `LLMClient`.
  - No schema, dependency, infrastructure, deployment, or public API shape
    change is present in the `origin/main...HEAD` diff.
  - The batch entry point can still call OpenAI and insert `ai_reports` rows
    when provided `DATABASE_URL` plus `OPENAI_API_KEY`; OpenAI key use now has
    standing user approval, while shared/dev DB writes remain separately
    approval-gated.
- **Verification**:
  - `git diff --name-status origin/main...HEAD`
  - `git diff --check origin/main...HEAD`
  - Dependency/schema/API path diff scan returned no matching changed files.
  - `cd backend && DATABASE_URL= pytest tests/test_ai_report_batch.py` — 17
    passed.
  - `cd backend && DATABASE_URL= pytest` — 117 passed.

## Follow-up Decision: OpenAI Key Approval

- **Date**: 2026-07-09
- **User clarification**: `OPENAI_API_KEY` was provided for this project and
  may be used without separate per-run approval.
- **Recorded in**: `memory/decisions.md` ADR-022.
- **Still separate**: shared/dev DB writes, schema/dependency/API shape changes,
  deployments, and infrastructure changes still require explicit approval.

## Follow-up Implementation: Scheduled Batch + Manual Reports

- **Date**: 2026-07-09
- **Agent Role**: Data/AI Implementer
- **Scope**: Implement the requested goals: generate current-DB AI summaries,
  connect data/metric/signal generation to AI summary generation, run the batch
  every 24h, and provide a development-only manual generation command without
  adding UI.
- **Work Completed**:
  - Added `backend/app/core/scheduled_batch.py`.
  - Added `.github/workflows/daily-batch.yml` with a 24h cron and manual
    `workflow_dispatch`.
  - Added `backend/tests/test_scheduled_batch.py`.
  - Updated `backend/README.md` with combined batch and `--reports-only`
    commands.
  - Updated `backend/app/core/ai_report_batch.py` stale approval wording for the
    project-approved OpenAI key.
- **Current DB Report Generation Attempt**:
  - Ran `ENV=local ./.venv/bin/python -m app.core.scheduled_batch
    --reports-only --confirm-local-dev-write`.
  - OpenAI returned `401 Unauthorized`; no successful summaries were stored.
  - Read-only counts after the run: `ai_reports_total=10`,
    `ai_reports_success=0`, `ai_reports_failed=10`.
  - The report endpoint still returns `not_yet_generated` for live issues.
- **Follow-up Current DB Report Generation Attempt**:
  - Reran `ENV=local ./.venv/bin/python -m app.core.scheduled_batch
    --reports-only --confirm-local-dev-write` after the user requested current
    DB summary generation again.
  - No process remained running afterward.
  - Read-only counts after the rerun: `ai_reports_total=20`,
    `ai_reports_success=0`, `ai_reports_failed=20`, `scheduled_batch_logs=2`.
  - Latest scheduled log: `scheduled_batch_partial` with
    `reports_success=0`, `reports_failed_or_filtered=10`,
    `reports_skipped=0`.
  - `GET /api/issues/{id}/report` for the first issue still returns
    `not_yet_generated`.
  - A same-client minimal OpenAI probe confirmed `OPENAI_API_KEY` is present,
    model is `gpt-4o-mini`, and the call fails with
    `OpenAI call failed: AuthenticationError`.
- **OpenAI Authentication Root Cause Check**:
  - A direct OpenAI SDK probe returned `status_code=401`,
    `code=invalid_api_key`.
  - The provider error message identifies the configured value as an incorrect
    API key for OpenAI. The masked key shape in the provider response appears
    to be an OpenRouter-style key, so the current OpenAI SDK default endpoint
    rejects it before any model call or quota check.
- **OpenRouter Support Implementation**:
  - Updated `backend/app/core/config.py` to select OpenRouter when
    `OPENROUTER_API_KEY` is present or `OPENAI_API_KEY` has the `sk-or-`
    prefix.
  - Kept the existing `openai` dependency and SDK call shape, but added
    `base_url`/provider/header support in `backend/app/core/ai_report.py`.
  - Updated `backend/app/core/scheduled_batch.py` and
    `backend/app/core/ai_report_batch.py` to use the resolved AI key, provider,
    endpoint, and model.
  - Added tests for provider detection, model slug conversion, and OpenRouter
    `base_url`/header propagation.
  - Recorded ADR-027 and updated architecture/project/known-issue notes.
- **Current DB AI Summary Generation via OpenRouter**:
  - Verified resolved provider settings without printing secrets:
    `provider=openrouter`, `base_url=https://openrouter.ai/api/v1`,
    `model=openai/gpt-4o-mini`; a minimal JSON probe succeeded.
  - First OpenRouter reports-only run stored 9 successful summaries and had one
    safety-filter rejection for `due to`.
  - Clarified the fixed system prompt to explicitly disallow causal connectors
    already enforced by the safety filter.
  - Found and fixed a reports-only selection gap: it previously used a single
    global latest metric timestamp, which skipped markets whose latest metric
    was a few seconds earlier. Reports-only now selects each market's latest
    metric row before applying the same no-report/stale-report cap.
  - Reran reports-only after the fix. Final read-only DB counts:
    `ai_reports_total=49`, `ai_reports_success=29`,
    `ai_reports_failed=20`, `scheduled_batch_logs=5`.
  - Latest scheduled log: `scheduled_batch_success`,
    `reports_success=10`, `reports_failed_or_filtered=0`,
    `reports_skipped=0`.
  - Verified `/api/issues?window=24h&sort=heat&limit=10` then
    `/api/issues/{id}/report`: all 10 checked issues returned
    `status=success` with content.
- **Verification**:
  - `cd backend && .venv/bin/ruff check app tests` — passed.
  - `cd backend && .venv/bin/pytest tests/test_ai_report.py
    tests/test_scheduled_batch.py tests/test_ai_report_batch.py` — 48 passed.
  - `cd backend && .venv/bin/pytest tests/test_scheduled_batch.py
    tests/test_ai_report_batch.py tests/test_signal_detection.py
    tests/test_snapshot_metrics.py` — 54 passed.
  - `cd backend && DATABASE_URL= .venv/bin/pytest` — 124 passed.
  - `git diff --check` — passed.

## Follow-up Local Server Restart

- **Date**: 2026-07-09
- **Agent Role**: Debugger
- **Scope**: Restart local development servers so implementation status can be
  checked in the browser.
- **Result**:
  - No existing listener was found on `127.0.0.1:8000` or `127.0.0.1:5173`.
  - Started backend with
    `ENV=local ./.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.
  - Started frontend with `npm run dev -- --host 127.0.0.1 --port 5173`.
  - Verified `GET /api/health` returns `200 OK`.
  - Verified backend and Vite proxy `/api/issues?window=24h&sort=heat&limit=1`
    return DB-backed data with `data_as_of=2026-07-09T06:26:04Z`.
- **Follow-up**:
  - No code, schema, dependency, infrastructure, deployment, or user-facing copy
    changes were made.
  - No task movement, new decision, new issue, or architecture update was
    required.

## Follow-up Implementation: TASK-043 Issue-Explainer Report Output

- **Date**: 2026-07-09
- **Agent Role**: Data/AI Implementer
- **Branch**: `data-ai/TASK-043-issue-explainer-report`
- **User approval**: The user approved changing the public report output/API
  shape from the original numeric 5-section summary to the new issue-explainer
  direction.
- **Work Completed**:
  - Advanced `backend/app/core/ai_report.py::PROMPT_VERSION` to `v2`.
  - Replaced the report content schema with 8 fixed slots:
    `issue_explainer`, `why_it_matters`, `current_reading`,
    `scenario_major_change`, `scenario_limited_change`,
    `scenario_status_quo`, `check_points`, and `caution_note`.
  - Updated the fixed prompt to generate plain-language Korean issue explainers
    for general readers, with neutral conditional scenario sections rather than
    value-loaded best/worst labels.
  - Kept strict JSON schema parsing and the existing banned-phrase/pattern
    safety filter before storage.
  - Updated `/api/issues/{id}/report` fallback/sample content and live read
    handling. Legacy stored v1 report content now returns
    `{"status":"not_yet_generated"}` instead of a mismatched success response.
  - Updated frontend report types, section labels, empty-state copy, and
    information notice copy for the issue-explainer format.
  - Updated `backend/API_CONTRACT.md`, Technical Design §10, ADR-028,
    `memory/architecture.md`, `memory/project.md`, `memory/known-issues.md`,
    `tasks/active.md`, `tasks/completed.md`, and
    `reports/task-043-issue-explainer-report.md`.
- **Verification**:
  - `cd backend && .venv/bin/ruff check app tests` — passed.
  - `cd backend && DATABASE_URL= .venv/bin/pytest tests/test_ai_report_batch.py tests/test_scheduled_batch.py tests/test_issues_live.py` — 42 passed.
  - `cd backend && DATABASE_URL= .venv/bin/pytest` — 130 passed.
  - `cd frontend && npm run typecheck` — passed.
  - `cd frontend && npm run lint` — passed.
  - `cd frontend && npm run build` — passed with the existing Recharts
    chunk-size warning.
  - `git diff --check` — passed.
  - Changed-string safety scans found only the documented prohibited-word list
    in prompts/docs and deleted legacy sample lines; no new Korean hard-block
    terms were found in changed UI/prompt content.
- **Notes / Remaining Risks**:
  - No DB schema change, dependency change, infrastructure change, deployment,
    or database write was performed.
  - The configured development DB may still contain v1 successful `ai_reports`
    rows. Those are now intentionally hidden as `not_yet_generated` until an
    approved reports-only run writes v2 summaries. Legacy `prompt_version` rows
    are treated as regeneration-eligible even when they are not yet stale.

## Follow-up Implementation: TASK-044 Korean Issue Display Titles

- **Date**: 2026-07-09
- **Agent Role**: Frontend Implementer
- **Branch**: `frontend/TASK-044-korean-issue-titles`
- **User request**: Main dashboard issue titles were hard to understand at a
  glance and appeared as raw English market questions. The requested direction
  was Korean issue display names plus 기준 조건, while preserving the source
  market title separately.
- **Work Completed**:
  - Added optional frontend issue display fields:
    `sourceTitle`, `displaySubtitle`, `topicLabel`, and
    `resolutionCondition`.
  - Added `frontend/src/utils/issueDisplay.ts` with deterministic display-copy
    mappings for the current live/demo issue set and conservative fallbacks for
    unseen titles.
  - Updated API-to-frontend mapping in `frontend/src/utils/format.ts`; no
    backend API shape change was made.
  - Updated dashboard cards, weekly rows, and detail headers to show Korean
    issue display names and one-line 기준 조건 first.
  - Preserved raw Polymarket titles only as detail-screen provenance text.
  - Updated static fallback/dummy issue construction to populate display
    subtitles from existing Korean descriptions.
  - Recorded ADR-029, `reports/task-044-korean-issue-titles.md`,
    `tasks/completed.md`, `tasks/active.md`, and `memory/project.md`.
- **Verification**:
  - `cd frontend && npm run typecheck` — passed.
  - `cd frontend && npm run lint` — passed.
  - `cd frontend && npm run build` — passed with the existing Recharts
    chunk-size warning.
  - Browser smoke at `http://127.0.0.1:5173/` confirmed dashboard cards show
    Korean titles/subtitles and detail headers show Korean title, 기준 조건, and
    source title provenance.
  - Changed-string safety scan passed; only code-level false positives such as
    `short` in formatter names remained.
  - `git diff --check` — passed.
- **Notes / Remaining Risks**:
  - No API, schema, dependency, infrastructure, deployment, database write, or
    backend behavior changed.
  - New unseen live market titles may need additional display-copy mapping
    polish later.

## Follow-up Review Fixes: PR #38 REQUEST_CHANGES

- **Date**: 2026-07-09
- **Agent Role**: Data/AI Implementer
- **Scope**: Resolve the two PR #38 review findings from the reviewer comment.
- **Work Completed**:
  - Updated `backend/app/core/scheduled_batch.py` so non-`reports_only` batch
    runs fail when no normalized markets are available. This prevents a live
    fetch returning zero records from being recorded as
    `scheduled_batch_success`.
  - Added `backend/tests/test_scheduled_batch.py` coverage proving empty
    normalized input records `scheduled_batch_failed`, performs no snapshot,
    metric, or report writes, and makes no LLM call.
  - Updated `.github/workflows/daily-batch.yml` to pass
    `OPENROUTER_API_KEY` from GitHub Actions secrets, matching ADR-027 and
    `backend/README.md`.
- **Verification**:
  - `cd backend && ./.venv/bin/ruff check app tests` — passed.
  - `cd backend && DATABASE_URL= ./.venv/bin/pytest tests/test_scheduled_batch.py`
    — 5 passed.
  - `cd backend && DATABASE_URL= ./.venv/bin/pytest tests/test_ai_report.py
    tests/test_ai_report_batch.py tests/test_scheduled_batch.py` — 49 passed.
  - `cd backend && DATABASE_URL= ./.venv/bin/pytest` — 125 passed.
  - `git diff --check` — passed.
- **Notes**:
  - No `.env` contents were printed or modified.
  - No schema, dependency, public API shape, deployment, real provider call, or
    database write was performed.
