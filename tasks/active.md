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
recorded in `reports/day-4-work-allocation.md`. With `TASK-040` complete, the
remaining active Day 4 work focuses on final wording safety.

| ID | Task | Owner | Assignee | Branch | Status |
|----|------|-------|----------|--------|--------|
| TASK-018 | Copy/wording lint pass across user-facing surfaces | PM | PM / Planner | `pm/TASK-018-copy-lint` | assigned |

Completed Day 1, Day 2, Day 3, and PM allocation tasks are archived in
`tasks/completed.md`, including `TASK-038` for this Day 4 allocation,
`TASK-015` (template report generation + safety filter, moved to
`tasks/completed.md` - see that file and ADR-022 for the OpenAI provider
override this task required and recorded), `TASK-039` (report API fallback
readiness), `TASK-016` (template report display UI), `TASK-019`
(curated related-event candidates), `TASK-041` (report-generation
readiness for historical-seed metric timestamps), `TASK-042` (combined
scheduled/manual report batch), `TASK-043` (v2 issue-explainer report
output structure), `TASK-044` (Korean issue display titles), and `ISS-007`
(v2 report/category-filter readiness).

## Day 4 Handoff Notes

- **PM / Planner** completed `TASK-038` in
  `reports/day-4-work-allocation.md`. PM completed the demo/deck draft
  (`TASK-040`) and still owns final copy lint (`TASK-018`).
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

## Active Task Details

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
