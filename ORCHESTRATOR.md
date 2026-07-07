<!--
Purpose:        Agent collaboration sequences and Human Approval Gates
Owner:          PM / Planner
Update Trigger: New workflow added, roles changed, approval policy updated
Harness Version: 1.1
-->

# ORCHESTRATOR.md — Outlook Signals Workflow Playbooks

_Last updated: 2026-07-07_

Five-day hackathon, four people. These playbooks assume each role above is a person pairing with an AI agent in that role — not four separate always-on agents. Keep every workflow short enough to run inside a single work session.

---

## PM Task Assignment Workflow

Run this workflow at the start of each project day before implementation begins.

```
[PM/Planner]  Review tasks/backlog.md for today's planned work
    ↓
Move selected work into tasks/active.md
    ↓
For each active task, assign Owner, Assignee, Branch, and Status
    ↓
[Role Agent]  Select only work assigned to its role or explicit Assignee
    ↓
Confirm or create the listed Branch before starting work
    ↓
On completion, move the task to tasks/completed.md during Session End Checklist
```

Rules:

- PM checks `tasks/backlog.md` before daily work starts.
- PM moves only today's selected work into `tasks/active.md`.
- Each active task must include `Owner`, `Assignee`, `Branch`, and `Status`.
- `Assignee` uses role names, not individual names.
- `Status` must be one of: `assigned`, `in_progress`, `blocked`, `review`, `completed`.
- Each role works only on tasks assigned to its role or explicit Assignee.
- Before any implementation, the worker confirms the current branch or creates/switches to the branch listed in `tasks/active.md`.
- Completed work moves from `tasks/active.md` to `tasks/completed.md` as part of the Session End Checklist.
- No one commits directly to `main` or `master`.

## Automation Script Design

These scripts are design targets only until explicitly implemented. Default behavior must always be preview-only. File writes and git branch operations are allowed only through a separate approval option or explicit user confirmation.

### `scripts/assign_tasks.py --day 1`

Purpose: assign planned work for a given project day from `tasks/backlog.md` into `tasks/active.md`.

Responsibilities:

- Read `tasks/backlog.md`.
- Find tasks matching the provided `--day` value.
- Select eligible work by `Owner`.
- Fill `Assignee` from the role mapping.
- Generate `Branch` using `[role-prefix]/[TASK-ID]-[short-kebab-slug]`.
- Set `Status` to `assigned`.
- Print a preview of proposed `tasks/active.md` changes before writing.
- Require PM approval before modifying task files.

### `scripts/start_task.py TASK-005`

Purpose: help a role agent start the correct active task on the correct branch.

Responsibilities:

- Accept a `TASK-ID` or `ISS-ID`.
- Find the matching row in `tasks/active.md`.
- Display `ID`, `Task`, `Owner`, `Assignee`, `Branch`, and `Status`.
- Check the current git branch.
- If already on the listed branch, confirm readiness.
- If not, propose the needed git switch/create command.
- Never run git branch commands by default.
- Execute git commands only after explicit user approval.
- Refuse direct work on `main` or `master`.

---

## Feature Workflow (Day 1–4 build work)

```
[PM/Planner]         Confirm feature is in P0/P1 scope (PRD §6.3–6.4) → add to tasks/backlog.md
    ↓
[Frontend/Backend/Data-AI Implementer]  Implement (whichever role owns the surface)
    ↓ ⚠️ HUMAN APPROVAL if new dependency, schema change, or scope creep into P2
[Reviewer]            Code review + wording/copy lint → note in reports/ if issues found
    ↓ ⚠️ HUMAN APPROVAL before merge to main
```

## BugFix Workflow

```
[Debugger]    Reproduce → root cause → register in memory/known-issues.md
    ↓
[Owning Implementer]  Fix
    ↓
[Reviewer]    Review
    ↓ ⚠️ HUMAN APPROVAL before deploy
```

## Data / AI Report Workflow (Data/AI Implementer specific — see Technical Design §9–10)

```
[Data/AI Implementer]  Compute metrics → build_prompt() from fixed template → call LLM
    ↓
Run banned-phrase safety filter (UX Design §5.3 list)
    ↓
  pass? → store in ai_reports table
  fail? → discard, log failure, keep previous report live (never auto-retry same prompt)
```

## Scope-Control Workflow (PM-owned, run daily per PRD §13.1)

```
[PM/Planner]  Check incoming feature requests against P0/P1/P2 tables (PRD §6.3–6.5)
    ↓
  In P0/P1? → route to tasks/backlog.md
  In P2 or new? → defer, log in roadmap.md "Backlog Ideas", do NOT implement without ⚠️ HUMAN APPROVAL
```

## Release / Demo-Readiness Workflow (Day 5)

```
[Reviewer]     Final review across all screens → confirm every data screen has timestamp + caution badge
    ↓
[Backend Implementer]  Deploy (Vercel + Railway/Render) → confirm static-JSON fallback works
    ↓
[PM/Planner]   Rehearse demo script, confirm Q&A sheet ready
    ↓ ⚠️ HUMAN APPROVAL for production deploy / going live for judging
```

---

## Human Approval Gates Summary

| Situation | Reason |
|-----------|--------|
| New external dependency | Setup/security review, and hackathon time cost |
| DB schema change | Irreversible change, blocks parallel frontend/backend work if wrong |
| Production deployment | Final responsibility stays with humans |
| Pulling a P1/P2 feature into MVP scope | Prevents the "trying to build everything at once" risk flagged in PRD §15.1 |
| Wording/safety policy change | Legal/ethical framing is core to this product (PRD §15.4) |
| Public API interface change | Breaks the frontend's contract (Technical Design §5) |
