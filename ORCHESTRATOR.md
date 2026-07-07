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
