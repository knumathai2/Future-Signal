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

- **Date**: 2026-07-10
- **Agent Role**: PM / Planner with Data/AI review
- **Session Goal**: Analyze how reviewed context candidates and v3 AI summaries
  can form one useful narrative while preserving the intent of the current
  product-safety constraints.
- **Branch**: `pm/TASK-055-context-summary-strategy`

## Context Read

- `AGENTS.md`
- Complete PRD, Service Design, Technical Design, and UX Design section sets
- `memory/project.md`, prior `memory/session.md`, `tasks/active.md`
- PM and Data/AI role prompts
- ADR-032 through ADR-035
- v3 API contract, AI prompt/assembly path, candidate loader/seed, report UI,
  wording standards, glossary, completed-task ledger, and known issues
- Read-only local API output for five current top issues

## Work Completed

- Created a clean worktree and role-compliant analysis branch without touching
  the user's dirty debugger worktree.
- Confirmed the policy intent is to block unsupported relationships,
  unreviewed public context, and open-ended model interpretation rather than to
  remove context itself.
- Traced the concrete disconnect:
  - candidate seed is local/development-only and outside the scheduled path;
  - the latest local DB sync records zero related events;
  - candidate fields exist in `ReportPromptInputs` but are excluded from the
    model prompt;
  - the loader reads one unordered candidate;
  - the report UI separates movement and context across one-at-a-time sections.
- Read five top-issue detail/report responses from localhost. Every detail
  response had an empty `related_events` list; successful v3 reports used
  `external_context=null` and the same candidate-absence text.
- Wrote the full analysis in
  `reports/task-055-context-candidate-ai-summary-strategy.md`.
- Converted the requested design direction into a one-person, 20-hour execution
  plan in `reports/task-055-automated-context-execution-plan.md`.
- Added proposed `TASK-056` through `TASK-065` to `tasks/backlog.md`, covering
  policy approval, append-only schema, OpenRouter research, deterministic and
  independent-model verification, batch storage, evidence-grounded v4 reports,
  Backend API, change-episode UI, integration review, and guarded backfill.
- Each proposed task now has an owner, role branch, time box, dependencies,
  file scope, acceptance criteria, validation commands, handoff, and stop
  conditions. The tasks remain inactive until `TASK-056` receives explicit
  approval.
- Added `reports/task-055-automated-context-stretch-plan.md` and proposed
  `TASK-066` through `TASK-074` for up to 25 additional hours after the core
  program. The priority order is evaluation harness, source registry,
  claim-level conflict checks, candidate revalidation, historical episodes,
  multilingual research, provenance UI, reliability controls, and a
  cross-issue event graph.
- Documented incremental stop points at +3h, +6h, +9h, +11h, +14h, +17h,
  +19.5h, +22h, and +25h so extra work can stop after a coherent quality tier.
- Recorded TD-013 and archived TASK-055 as completed.
- Preserved the prior local runtime/DB-sync handoff in
  `memory/sessions/2026-07-10-Debugger-local-db-sync.md`.

## Main Finding

The current requested target is a **change episode** backed by an
**automatically verified evidence bundle**. Deterministic URL/date/domain/entity
gates and an independent verifier replace recurring human candidate review;
conditions that do not pass are hidden. The writing model receives only the
verified bundle and cannot add candidate URLs, decide relationships, or add
external facts.

This changes the validation unit from field length and blocked wording alone
to evidence provenance, sentence type, metric/candidate references, and a
mandatory statement that the relationship is not established.

## Verification

- Documentation-only diff inspected.
- Read-only local API checks succeeded; no remote access or database write was
  performed.
- Project wording scan on the changed analysis/session/task/issue files found
  no unintended hard-block wording outside code identifiers and policy-facing
  references.
- `git diff --check` passed.

## Approval Boundaries / Follow-up

- No product decision was accepted and no implementation was performed.
- Existing schema/policy can support a first recovery step: choose live
  representative issues, manually curate Korean candidate notes, seed only
  after approval, regenerate reports through the approved path, and add a
  candidate-coverage check.
- The proposed fully automated path is now decomposed into `TASK-056`~`TASK-065`
  but remains backlog-only. No task should move to active before the policy,
  provider budget, schema, API, and local/dev-write gates are accepted.
- Optional `TASK-066`~`TASK-074` also remain backlog-only and cannot start until
  `TASK-065` closes. Stretch schema/API additions outside TASK-056's accepted
  scope require a separate approval addendum.
- Letting the model receive approved candidates, changing ADR-033 display
  order/report shape, or changing ADR-034 assembly behavior needs a follow-up
  ADR and user review.
- Source URL/review-status/episode-link fields require schema and likely public
  API approval.
- Scheduled external context collection or public automated matching remains
  out of scope unless a later approved policy explicitly changes that boundary.
- No code, DB, API, policy, dependency, infrastructure, deployment, external
  provider call, or database write changed during TASK-055.
