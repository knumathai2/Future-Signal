<!--
Purpose:        Track currently in-progress tasks
Owner:          Implementer roles / PM
Update Trigger: Task started, completed, or blocked
Harness Version: 1.1
-->

# Active Tasks — Outlook Signals

_Last updated: 2026-07-09_

## In Progress

Day 4 is now active from latest `origin/main` at `af83f7e`, which includes
the Day 3 closeout merge. Allocation evidence is recorded in
`reports/day-4-work-allocation.md`. Day 4 focuses on template summaries,
report display, manual event candidates, demo-story preparation, fallback
readiness, and final wording safety.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-019 | Curated related-event candidates for representative issues | PM + Data/AI | Data/AI Implementer + PM / Planner | `data-ai/TASK-019-curated-events` | assigned |
| TASK-040 | Day 4 demo script and deck draft | PM | PM / Planner | `pm/TASK-040-demo-script-deck-draft` | assigned |
| TASK-018 | Copy/wording lint pass across user-facing surfaces | PM | PM / Planner | `pm/TASK-018-copy-lint` | assigned |

Completed Day 1, Day 2, Day 3, and PM allocation tasks are archived in
`tasks/completed.md`, including `TASK-038` for this Day 4 allocation,
`TASK-015` (template report generation + safety filter, moved to
`tasks/completed.md` - see that file and ADR-022 for the OpenAI provider
override this task required and recorded), and `TASK-039` (report API
fallback readiness), and `TASK-016` (template report display UI).

## Day 4 Handoff Notes

- **PM / Planner** completed `TASK-038` in
  `reports/day-4-work-allocation.md`. PM owns the demo/deck draft (`TASK-040`)
  and final copy lint (`TASK-018`), and co-reviews manual event candidate copy
  in `TASK-019`.
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
- **Reviewer / Debugger** stay embedded. Any user-facing string changed during
  Day 4 must pass the project wording lint before review.

## Active Task Details

### TASK-019: Curated related-event candidates for representative issues
- **Owner**: PM + Data/AI
- **Assignee**: Data/AI Implementer + PM / Planner
- **Branch**: `data-ai/TASK-019-curated-events`
- **Status**: assigned
- **Priority**: High
- **Day**: Day 4
- **Description**: Select 3-5 representative issues and create manual context
  candidates that can be shown beside observed changes in the demo.
- **Definition of Done**:
  - [ ] Selects exactly 3-5 representative demo issues from existing live,
        normalized, or fallback issue IDs.
  - [ ] Each candidate includes title, date, and note text that explicitly
        frames it as context, not a cause.
  - [ ] Provides a seed/local-dev insertion path or artifact using existing
        `related_events` schema boundaries only.
  - [ ] Does not build automated event matching or write directly to a shared
        or production database.
  - [ ] PM runs a wording review before the candidates feed the demo script.

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
