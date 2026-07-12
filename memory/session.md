<!--
Purpose:        Current session handoff only
Owner:          Currently active agent
Update Trigger: Every session
Harness Version: 1.1
-->

# Current Session — Outlook Signals

_Last updated: 2026-07-12_

Git history preserves earlier session states; do not create per-session archive
files.

## Session

- **Role**: PM / Planner
- **Branch**: `pm/TASK-123-scenario-chatbot-plan`
- **Goal**: Plan a freer current summary and secure scenario conversation.
- **Status**: Completed

## Completed in TASK-123

- Separated the stable current summary from a flexible issue-scoped scenario
  conversation.
- Defined server-owned premise classes so assumptions cannot become current
  facts across turns.
- Chose a tool-free, read-only model boundary with no database, browser, URL,
  secret, or side-effect access.
- Documented prompt-injection, indirect-source, session-isolation, output,
  privacy, cost, conventional API, and operational controls.
- Proposed TASK-124~131 with independent policy, API, schema, provider,
  infrastructure, migration, deployment, and activation gates.
- Added acceptance, evaluation, rollout, rollback, and open-decision sections.

## Boundaries

- This is a proposal and Phase 2 backlog record only.
- No active wording policy, user-facing runtime text, code, public API, schema,
  dependency, provider call, database, infrastructure, deployment, or
  production state changed.
- Active v8 and all existing approval boundaries remain unchanged.

## Next handoff

Review the TASK-123 plan. If its direction is accepted, approve and start only
TASK-124 (policy lock) and TASK-125 (threat/API/storage proposal) before any
implementation. TASK-122 remains in review on its existing branch.
