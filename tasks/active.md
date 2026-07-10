<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-10_

## In Progress

Day 4 is closed. Allocation evidence is recorded in
`reports/day-4-work-allocation.md`, the final copy lint is recorded in
`reports/task-018-copy-lint.md`, and closeout evidence is recorded in
`reports/day-4-closeout-plan.md`.

`TASK-047` and `TASK-048` are complete. ADR-033 supersedes ADR-032 for the
approved eight-field v3 report content and display contract. Frontend, Backend,
and Data/AI v3 implementation must read both ADRs, follow ADR-033 where they
differ, and keep runtime changes in separate coordinated tasks. Day 5 v3
implementation allocation evidence is recorded in
`reports/day-5-v3-implementation-allocation.md`.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-049 | Implement v3 report generation content | Data/AI Implementer | Data/AI Implementer | `data-ai/TASK-049-v3-report-generation` | review |
| TASK-050 | Implement v3 report API/read contract | Backend Implementer | Backend Implementer | `backend/TASK-050-v3-report-runtime` | assigned |
| TASK-051 | Implement v3 dynamic report UI | Frontend Implementer | Frontend Implementer | `frontend/TASK-051-v3-report-cards` | review |
| TASK-053 | Review v3 integration copy and contract | Reviewer | Reviewer | `review/TASK-053-v3-report-copy-lint` | assigned |

Completed Day 1, Day 2, Day 3, and PM allocation tasks are archived in
`tasks/completed.md`, including `TASK-038` for this Day 4 allocation,
`TASK-015` (template report generation + safety filter, moved to
`tasks/completed.md` - see that file and ADR-022 for the OpenAI provider
override this task required and recorded), `TASK-039` (report API fallback
readiness), `TASK-016` (template report display UI), `TASK-019`
(curated related-event candidates), `TASK-041` (report-generation
readiness for historical-seed metric timestamps), `TASK-042` (combined
scheduled/manual report batch), `TASK-043` (v2 issue-explainer report
output structure), `TASK-044` (Korean issue display titles), `ISS-007`
(v2 report/category-filter readiness), and `TASK-018` (final copy/wording
lint). `TASK-045` records the PM closeout verification and Day 5 handoff.
`TASK-047` records the v3 AI report policy/API/wording scope-lock and
implementation prerequisite decision in ADR-032. `TASK-048` records the
superseding eight-field contract in ADR-033. `TASK-052` records the latest
git-state check and Day 5 v3 implementation allocation.

## Day 5 Allocation Notes

- **PM / Planner** completed `TASK-038` in
  `reports/day-4-work-allocation.md`. PM completed the demo/deck draft
  (`TASK-040`) and final copy lint (`TASK-018`).
- **Data/AI Implementer** completed `TASK-015` on
  `data-ai/TASK-015-template-report-generation` (see `tasks/completed.md`).
  Note for `TASK-016`/`TASK-018`: contrary to this file's original Day 4
  default, the user explicitly approved wiring a real OpenAI call (ADR-022)
  rather than stubbing it - `openai` is now a real dependency and
  `OPENAI_API_KEY`/`OPENAI_MODEL` are real settings, though no key is present
  in this environment so no live call has actually executed yet.
- **Backend Implementer** completed `TASK-039` in the PR #29 follow-up.
  `/api/issues/{id}/report` now preserves the accepted response shape, reads
  latest successful `ai_reports` rows in live mode, and keeps the neutral empty
  state when no successful report is available.
- **Frontend Implementer** completed `TASK-016` against the accepted report
  shape. The summary area now handles success, not-yet-generated, loading, and
  fetch-failure states with data-as-of timing and interpretation-caution
  context nearby.
- **Data/AI Implementer + PM** completed `TASK-019` in PR #36. The branch added
  `backend/app/db/seed_related_events.py` with exactly 4 manually curated,
  normalized/live-reachable issue IDs plus tests for safety wording and schema
  boundaries.
- **Data/AI Implementer** completed `TASK-041`. Report prompt inputs now use the
  latest snapshot at or before the metric timestamp, preserving the no-fabrication
  skip path when no usable prior snapshot exists. OpenAI report calls are covered
  by ADR-022 and the provided-key clarification; any write to the configured
  development DB remains separately approval-gated.
- **Data/AI Implementer** completed `TASK-043`. The AI report content shape is
  now the v2 issue-explainer schema with neutral conditional scenario sections.
  Existing v1 stored report content is treated as `not_yet_generated` until a
  separately approved reports-only run writes v2 summaries.
- **PM / Planner** completed `TASK-040`. The deck outline, demo script,
  fallback narration, Day 5 screenshot/rehearsal checklist, and judge Q&A draft
  are recorded in `reports/task-040-demo-script-deck-draft.md`; the reusable
  startup prompt is recorded in
  `reports/task-040-demo-script-deck-draft-prompt.md`.
- **Frontend Implementer** completed `TASK-044`. Dashboard and detail headings
  now show Korean issue display names and 기준 조건 first, with raw Polymarket
  titles preserved only as detail-screen provenance.
- **Debugger** resolved `ISS-007`. Report reads now require current v2 content,
  report regeneration handles same-timestamp rows correctly, and the top-level
  category filters remain broad Korean groups while detailed topic labels stay
  in the card/detail display layer.
- **Reviewer / Debugger** stay embedded. Any user-facing string changed during
  Day 4 must pass the project wording lint before review.
- **PM / Planner** completed `TASK-045`. Day 4 is closed and Day 5 starts from
  the closeout record in `reports/day-4-closeout-plan.md`.
- **PM / Planner** completed `TASK-047`. ADR-032 locks the v3 report field
  list, public API boundary, tightened wording criteria, manual-only context
  candidate scope, and maintained prohibitions before v3 implementation starts.
- **Backend Implementer** completed `TASK-048`. ADR-033 preserves ADR-032 as
  history while superseding its v3 content/display contract with the approved
  eight-field schema. Runtime remains v2 pending coordinated implementation.
- **PM / Planner** completed `TASK-052`. Latest `origin/main` is
  `106af52`, which includes PR #45 (`TASK-047`) and PR #46 (`TASK-048`).
  Runtime remains v2, but Day 5 v3 work is now split across Data/AI,
  Backend, Frontend, and Reviewer tasks.
- **Data/AI Implementer** completed implementation for `TASK-049` (status
  `review`, pending Reviewer/PM close-out alongside `TASK-050`/`TASK-051`).
  `app/core/ai_report.py` now targets `PROMPT_VERSION = "v3"`: the LLM prompt
  asks only for `issue_overview`, `current_data_reading`, and
  `possible_outlook`; `possible_drivers`, `external_context`, `what_to_check`,
  `data_limitations`, and `caution_note` are assembled deterministically from
  `ReportPromptInputs` and merged by `assemble_report_content()` into the
  frozen ADR-033 eight-field `ReportContent` (this module's own structural
  copy of the contract, kept separate from `app/schemas/issues.py` per the
  parallelization plan so Backend's `TASK-050` schema edits don't collide).
  See ADR-034 for the full design rationale. `app/core/ai_report_batch.py`
  now also resolves the tracked outcome label and curated related-event
  title/date/note separately from `Market`/`MarketOutcome`/`RelatedEvent`.
  Safety validation gained the ADR-033 Korean hard-block terms, Korean
  causal/forecast patterns, and new `run_semantic_checks` cross-field checks
  (exact caution literal, exact possible_drivers literal, external_context
  candidate-not-cause qualifier). Tests cover valid v3 assembly, malformed/
  short-field rejection, English+Korean banned wording, weak-inference
  blocking, and no-candidate behavior in `tests/test_ai_report.py` and
  `tests/test_ai_report_batch.py`; `tests/test_scheduled_batch.py`'s fake LLM
  fixture was updated to the new three-field response shape. No real provider
  call or configured/shared DB write was made or is needed for this task.
- **Backend Implementer** owns `TASK-050`. Implement the ADR-033 report
  schema/read contract and version gating. Backend owns shared API/Pydantic
  schema edits so Data/AI and Frontend can avoid duplicate contract changes.
- **Frontend Implementer** owns `TASK-051`. Replace fixed v2 report-section
  rendering with dynamic ADR-033 sections, displayed as a single visible card
  section at a time, while hiding `external_context` only when it is `null`.
- **Reviewer** owns `TASK-053`. Start after the implementation branches are
  ready for integration, and run copy/wording, response-shape, mobile, and
  data-as-of/caution checks before any demo data refresh or deployment.
- **Parallelization**: `TASK-049`, `TASK-050`, and `TASK-051` can begin in
  parallel from ADR-033. Coordinate the shared `ReportContent`/API contract
  surface through `TASK-050`; `TASK-053` is sequential and should review the
  integrated result.

## Active Task Details

### TASK-049: Implement v3 report generation content
- **Owner**: Data/AI Implementer
- **Assignee**: Data/AI Implementer
- **Branch**: `data-ai/TASK-049-v3-report-generation`
- **Status**: review
- **Priority**: High
- **Day**: Day 5
- **Description**: Replace runtime report generation with ADR-033 v3 content:
  `issue_overview`, `current_data_reading`, `possible_outlook`,
  `possible_drivers`, `external_context`, `what_to_check`,
  `data_limitations`, and `caution_note`. Preserve maintained prohibitions,
  conditional public-data wording, non-causal context language, and
  deterministic caution behavior.
- **Definition of Done**:
  - [x] Generated content validates against ADR-033 fields, nullability, and
        Unicode character bounds.
  - [x] `external_context` uses only PM/Data-reviewed narrative notes and is
        `null` when approval or content is unavailable.
  - [x] `possible_drivers` uses reviewed title/date candidates only as
        comparison context, never as cause.
  - [x] `caution_note` and `data_limitations` cover all required caution and
        limitation language, including low-data cases.
  - [x] Tests cover valid v3 output, malformed output rejection, banned wording,
        weak-inference blocking, and no-candidate behavior.
  - [x] No live provider call or configured DB write is performed without
        separate approval.

### TASK-050: Implement v3 report API/read contract
- **Owner**: Backend Implementer
- **Assignee**: Backend Implementer
- **Branch**: `backend/TASK-050-v3-report-runtime`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 5
- **Description**: Move the report read path and shared schema from current v2
  runtime behavior to the approved ADR-033 v3 content contract while preserving
  the existing endpoint path and neutral empty-state behavior.
- **Definition of Done**:
  - [ ] Shared Pydantic/API schemas enforce the ADR-033 eight-field content
        shape, required nullable `external_context`, and extra-field rejection.
  - [ ] `/api/issues/{id}/report` serves only current v3 successful report rows
        and keeps `not_yet_generated` for absent, failed, or legacy rows.
  - [ ] Contract tests cover success, null `external_context`, legacy version
        exclusion, not-yet-generated, and unknown issue paths.
  - [ ] API contract documentation stays aligned with runtime behavior.
  - [ ] No migration, dependency, infrastructure, deployment, or unapproved DB
        write is introduced.

### TASK-051: Implement v3 dynamic report UI
- **Owner**: Frontend Implementer
- **Assignee**: Frontend Implementer
- **Branch**: `frontend/TASK-051-v3-report-cards`
- **Status**: review
- **Priority**: High
- **Day**: Day 5
- **Description**: Replace fixed v2 report rendering with a dynamic ADR-033
  section renderer. Display the report as a card-style flow where only one
  field is visible at a time, using the evidence-first order and Korean labels
  approved in ADR-033.
- **Definition of Done**:
  - [ ] Frontend report types match ADR-033 exactly.
  - [ ] Sections render in this order: `issue_overview`,
        `current_data_reading`, `external_context`, `possible_drivers`,
        `possible_outlook`, `what_to_check`, `data_limitations`,
        `caution_note`.
  - [ ] `external_context` is hidden only when the value is `null`; other empty
        or missing required fields are treated as invalid/error state.
  - [ ] One-section-at-a-time card navigation works on desktop and mobile
        without text overflow or layout shift.
  - [ ] Data-as-of timing and interpretation-caution context remain near the
        report experience.
  - [ ] Frontend typecheck, lint, build, and browser responsive checks pass.

### TASK-053: Review v3 integration copy and contract
- **Owner**: Reviewer
- **Assignee**: Reviewer
- **Branch**: `review/TASK-053-v3-report-copy-lint`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 5
- **Description**: Review the integrated v3 report runtime, UI, and copy before
  any report refresh, screenshot capture, or deployment.
- **Definition of Done**:
  - [ ] ADR-033 field names, labels, order, nullability, and response-shape
        behavior match Backend and Frontend runtime code.
  - [ ] User-facing strings pass `standards.md`, `memory/glossary.md`, and
        ADR-033 wording-safety checks.
  - [ ] No outcome assertion, action language, individual participant analysis,
        causal event explanation, or probability-as-real-world-result wording
        ships.
  - [ ] Every data-bearing report state has nearby data-as-of and caution
        context.
  - [ ] Integration test/build evidence is recorded before PM closeout.

## Status Values

`assigned` | `in_progress` | `blocked` | `review` | `completed`

## Row Examples

These rows show the required format only. Do not treat them as active assignments unless the PM moves them into `In Progress`.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-XXX | Example PM task | PM | PM / Planner | `pm/TASK-XXX-example-task` | assigned |
| TASK-YYY | Example frontend task | Frontend Implementer | Frontend Implementer | `frontend/TASK-YYY-example-task` | assigned |
| TASK-ZZZ | Example backend task | Backend Implementer | Backend Implementer | `backend/TASK-ZZZ-example-task` | assigned |
| ISS-XXX | Example debugging task | Debugger | Debugger | `debug/ISS-XXX-example-issue` | assigned |

## Task Detail Template

```
### TASK-XXX: [Title]
- **Owner**: [PM | Frontend Implementer | Backend Implementer | Data/AI Implementer]
- **Assignee**: [PM / Planner | Frontend Implementer | Backend Implementer | Data/AI Implementer]
- **Branch**: [role-prefix]/[TASK-ID]-[short-kebab-slug]
- **Status**: assigned | in_progress | blocked | review | completed
- **Priority**: High | Medium | Low
- **Day**: Day [1-5]
- **Description**:
- **Definition of Done**:
  - [ ] [Condition 1]
  - [ ] [Condition 2]
```
