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
- **Session Goal**: Implement TASK-015 (fixed-template AI report generation
  function and the banned-phrase safety filter).
- **Branch**: `data-ai/TASK-015-template-report-generation`

## Previous Session Summary

Day 4 was opened by `TASK-038` (PM allocation, `af83f7e`), which moved
`TASK-015`, `TASK-039`, `TASK-016`, `TASK-019`, `TASK-040`, and `TASK-018`
into `tasks/active.md` and defaulted `TASK-015`'s execution to deterministic
template generation (no live LLM call) pending separate paid-API approval. A
concurrent Backend Implementer session resolved PR #29 `CHANGES_REQUESTED`
feedback and completed `TASK-039` on `backend/TASK-039-stabilize-api-fallback`
in parallel with this session; its full session record is archived at
`memory/sessions/2026-07-09-Backend-Implementer-pr29-changes-requested-resolution.md`.
Merging that work into this branch produced an ADR-021 numbering collision
(see below) and the conflicts resolved across `tasks/active.md`,
`tasks/completed.md`, and the `memory/` ledger files.

## Current Work

- [x] Read `AGENTS.md`, Technical Design §9-10, UX Design §5.3, `standards.md`.
- [x] Found local `main` was stale (only through Day 1); fetched
      `upstream/main` and branched `data-ai/TASK-015-template-report-generation`
      from it, which already carried the real Day 4 allocation (PM had already
      moved `TASK-015` into `tasks/active.md` there - the "still only in
      backlog.md" case in this task's instructions did not apply once synced).
- [x] Surfaced a real conflict to the user before writing code: the Day 4
      allocation's default for `TASK-015` is deterministic template generation
      with any real LLM provider hook "disabled or stubbed until approved,"
      which is stricter than Technical Design §9-10's live-LLM-call
      architecture. Asked the user how to reconcile it.
- [x] User chose OpenAI as provider, then explicitly chose to override the
      Day 4 deterministic default and wire a real OpenAI call - recorded as
      ADR-022 (⚠️ HUMAN APPROVAL, both the paid-API-call gate and the
      AI-Provider-Selection gate; ADR-021 was already taken by a concurrent
      Backend Implementer session's report-read-path decision, discovered
      while resolving the merge conflict this created).
- [x] Implemented `backend/app/core/ai_report.py`: fixed §10.1 system prompt
      and §10.2 user prompt template (`build_prompt()`, zero free-text
      insertion points beyond the named slots), `LLMClient` protocol +
      `OpenAIReportClient` (real OpenAI Chat Completions call, JSON mode),
      strict schema parse (`parse_report_content()` via `ReportContent` with
      `extra="forbid"` added to `app/schemas/issues.py`), and the
      banned-phrase/pattern safety filter (`run_safety_filter()`).
- [x] Implemented `backend/app/core/ai_report_batch.py`: regeneration
      eligibility (new signal this run / no successful report yet / latest
      successful report >24h stale), capped to top 10 by `heat_score`,
      exactly-one-retry on LLM-call or malformed-schema failure then
      `status=failed`, and discard-without-retry on a safety-filter failure -
      in every failure case the previous successful `ai_reports` row is left
      untouched and keeps serving.
- [x] Added `openai==2.44.0` to `backend/requirements.txt` (new dependency,
      approved alongside the provider decision) and `OPENAI_API_KEY`/
      `OPENAI_MODEL` to `app/core/config.py`/`.env.example`.
- [x] Wrote `tests/test_ai_report.py` and `tests/test_ai_report_batch.py` (38
      new tests, 100 total) against a fake `LLMClient` - no real network call
      made or needed for the suite to pass.
- [x] Found and fixed a real bug during testing: word-boundary regex (`\b`)
      treats `-` as a boundary, so the banned word "short" false-positive
      matched "short-term" - which appears verbatim in Technical Design
      §10.3's own reference example output. Fixed with a custom boundary
      `(?<![\w-])...(?![\w-])` so hyphenated compounds like "short-term"/
      "long-term"/"trade-off" are not rejected while standalone usage still is.
- [x] Verified Technical Design §10.3's literal reference example round-trips
      through the parser and passes the filter clean (added as a regression
      test - explicit DoD "exact tone and format" check).
- [x] `ruff check .` clean across the whole backend, `pytest` 100/100 passing.
- [x] Moved `TASK-015` from `tasks/active.md` to `tasks/completed.md`.
- [x] Recorded ADR-022 in `memory/decisions.md`.
- [x] Resolved a merge with `upstream/main`'s `TASK-039` completion (PR #29
      follow-up), including an ADR-021 number collision - both sessions
      independently used ADR-021; renumbered this session's entry to ADR-022
      and kept Backend Implementer's ADR-021 as-is.
- [x] Resolved PR #30 `CHANGES_REQUESTED` feedback by updating
      `dependencies.md` so the concrete `openai==2.44.0` package, OpenAI API
      provider choice, and ADR-022 human-approval/cost gate are recorded in
      the dependency ledger.

## Issues Found / Decisions Made

- ADR-022: OpenAI selected as AI provider; real client wired; user explicitly
  approved overriding the Day 4 deterministic-template default. No
  `OPENAI_API_KEY` is present in this development environment, so **no real/
  billed API call has actually been executed** - this is architecture +
  approval, not a live-tested call. Whoever runs this against a real key for
  the first time (demo prep or `TASK-039`/`TASK-016` integration testing)
  should treat that as the first real cost-incurring event and watch it.
- This task intentionally does **not** touch `app/api/routes/issues.py` -
  wiring `ai_reports` rows into the live `GET /api/issues/{id}/report`
  response is `TASK-039`'s scope (Backend Implementer), not this task's.
- `ReportContent` (`app/schemas/issues.py`) gained `model_config =
  ConfigDict(extra="forbid")`. This tightens validation (an LLM response with
  an extra field now fails parse rather than being silently trimmed) but does
  not change the wire shape of the accepted `IssueReportResponse` contract.
- No schema migration, no shared/production database write, no deployment,
  and no public API interface change was made. The `ai_reports` table/model
  already existed (from `TASK-002`, still unapplied to any real database).
- PR #30 review feedback found that `backend/requirements.txt` selected
  `openai==2.44.0` while `dependencies.md` still listed only the generic
  provider candidate. The dependency ledger now names the concrete package,
  selected API provider, approval date, and ADR-022 reference.

## Verification

- `pytest tests/` → 100/100 passed (62 pre-existing + 38 new) during the
  initial TASK-015 implementation.
- PR #30 review-follow-up verification: `.venv/bin/python -m pytest` →
  104/104 passed after installing `openai==2.44.0`.
- PR #30 review-follow-up verification: `.venv/bin/python -m ruff check .` →
  all checks passed, whole backend.
- PR #30 review-follow-up verification: `git diff --check` → passed.
- Manual smoke: Technical Design §10.3's exact reference JSON parses via
  `parse_report_content()` and passes `run_safety_filter()` clean.
- Manual smoke: `OpenAIReportClient.complete()` correctly wraps a real
  `openai.APITimeoutError` (constructed via `httpx.Request`) into
  `LLMCallError`, and raises on an empty-choices response.
- No live OpenAI network call was made anywhere in this session (no API key
  configured in this environment).

## Next Session: To-Do

1. `TASK-039` is now complete (concurrent Backend Implementer session, PR #29
   follow-up) - `GET /api/issues/{id}/report` already reads the latest
   `status="success"` `ai_reports` row this task's storage shape produces.
2. Before any live/demo run of `app/core/ai_report_batch.py` with a real
   `OPENAI_API_KEY`, confirm the key is scoped/budgeted (ADR-022's
   consequence note) - this is the first point real API cost becomes possible.
3. Frontend Implementer (`TASK-016`) can proceed against the accepted
   `IssueReportResponse`/`ReportNotYetGenerated` shape - `TASK-039` has landed.
4. PM (`TASK-018`) should include `app/core/ai_report.py`'s `SYSTEM_PROMPT`/
   `USER_PROMPT_TEMPLATE` and the banned-phrase/pattern lists in the Day 4
   copy/wording lint pass, alongside UI strings.
5. `TD-009` remains open (backend static fallback sample issue titles can
   differ from the Korean frontend fallback) - see the Backend Implementer's
   archived session for its precise Day 5 fallback/demo note.
6. Reviewer should re-review PR #29 after this branch is pushed.
