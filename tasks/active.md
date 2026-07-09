<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-09_

## In Progress

Day 4 is now active from latest `origin/main` at `6d0eb44`, which includes
the merged `TASK-019` related-event candidate work. Allocation evidence is
recorded in `reports/day-4-work-allocation.md`. Day 4 now focuses on closing
AI report generation readiness, demo-story preparation, and final wording
safety.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-041 | AI report generation readiness for live demo data | Data/AI | Data/AI Implementer | `data-ai/TASK-041-report-generation-readiness` | assigned |
| TASK-040 | Day 4 demo script and deck draft | PM | PM / Planner | `pm/TASK-040-demo-script-deck-draft` | assigned |
| TASK-018 | Copy/wording lint pass across user-facing surfaces | PM | PM / Planner | `pm/TASK-018-copy-lint` | assigned |

Completed Day 1, Day 2, Day 3, and PM allocation tasks are archived in
`tasks/completed.md`, including `TASK-038` for this Day 4 allocation,
`TASK-015` (template report generation + safety filter, moved to
`tasks/completed.md` - see that file and ADR-022 for the OpenAI provider
override this task required and recorded), `TASK-039` (report API fallback
readiness), `TASK-016` (template report display UI), and `TASK-019`
(curated related-event candidates).

## Day 4 Handoff Notes

- **PM / Planner** completed `TASK-038` in
  `reports/day-4-work-allocation.md`. PM owns the demo/deck draft (`TASK-040`)
  and final copy lint (`TASK-018`).
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
- **Data/AI Implementer** owns the new `TASK-041` readiness gap. The configured
  development DB currently has `ai_reports=0`; latest historical-seed metric
  timestamps are slightly after snapshot timestamps, while the current report
  batch input builder requires exact timestamp equality. This blocks generating
  stored summaries from the latest seeded metric run until fixed or a compatible
  run is selected.
- **Reviewer / Debugger** stay embedded. Any user-facing string changed during
  Day 4 must pass the project wording lint before review.

## Active Task Details

### TASK-041: AI report generation readiness for live demo data
- **Owner**: Data/AI
- **Assignee**: Data/AI Implementer
- **Branch**: `data-ai/TASK-041-report-generation-readiness`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 4
- **Description**: Ensure the stored template-summary path can produce and
  serve successful `ai_reports` rows for representative live/dev issues. The
  frontend report card and read API are implemented, but the configured dev DB
  has no successful stored summaries yet. The report batch currently looks up a
  snapshot with `MarketSnapshot.captured_at == MarketMetric.computed_at`, while
  `historical_seed` intentionally writes metric timestamps one microsecond after
  the latest snapshot timestamp.
- **Definition of Done**:
  - [ ] Starts from latest `origin/main` at `6d0eb44` or newer.
  - [ ] Adds test coverage showing `ai_report_batch` can build prompt inputs
        when `market_metrics.computed_at` is slightly after the latest snapshot
        timestamp, as produced by `historical_seed`.
  - [ ] Adjusts report input lookup to use the latest snapshot at or before the
        metric run timestamp instead of requiring exact timestamp equality,
        without fabricating values.
  - [ ] Verifies `run_ai_report_batch` can insert `status=success` rows with a
        fake `LLMClient` in tests.
  - [ ] Preserves the public API shape: `/api/issues/{id}/report` still returns
        either the accepted success response or `{"status":"not_yet_generated"}`.
  - [ ] Adds local/demo run notes explaining how to generate stored summaries
        after the required approval, including the expected no-report empty
        state when no approved write/API call has run.
  - [ ] Does not change schema, dependencies, infrastructure, deployment, or
        public API interfaces.
  - [ ] Does not call OpenAI or write to a shared/dev database unless the user
        explicitly approves that run.

### TASK-040: Day 4 demo script and deck draft
- **Owner**: PM
- **Assignee**: PM / Planner
- **Branch**: `pm/TASK-040-demo-script-deck-draft`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 4
- **Description**: Draft the presentation deck and demo script so the Day 5
  session can focus on rehearsal, deployment readiness, and final Q&A.
- **Definition of Done**:
  - [ ] Deck outline covers problem, current alternatives, product flow,
        safeguards, implementation realism, and next-step story.
  - [ ] Demo script follows Home -> Detail -> Chart -> Summary -> caution
        notice -> manual context candidate.
  - [ ] Includes a fallback narration if live/local data is unavailable.
  - [ ] Keeps the product framed as an issue-monitoring tool and avoids
        outcome assertions or action-inducing language.
  - [ ] Leaves Day 5 with a clear list of final slides, screenshots, and
        rehearsal items.

### TASK-018: Copy/wording lint pass across user-facing surfaces
- **Owner**: PM
- **Assignee**: PM / Planner
- **Branch**: `pm/TASK-018-copy-lint`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 4
- **Description**: Run the project content-safety lint across all changed
  Day 4 user-facing strings, templates, report content, event candidates, and
  demo/deck copy.
- **Definition of Done**:
  - [ ] Checks frontend UI strings, backend fallback/report strings, report
        templates, event candidates, and demo/deck copy against `standards.md`
        and `memory/glossary.md`.
  - [ ] Records the lint result in a report or session note.
  - [ ] Confirms every data-bearing surface has nearby data-as-of timing and
        interpretation-caution context.
  - [ ] Does not change the wording policy itself without human approval.
  - [ ] Any hard-block finding is fixed or explicitly blocks Day 4 closeout.

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
