# Day 5 v3 Implementation Allocation

_Date: 2026-07-10_
_Owner: PM / Planner_
_Branch: `pm/TASK-052-v3-implementation-allocation`_

## Source State

- Latest checked remote state: `origin/main` at `106af52`
  (`Merge pull request #46 from knumathai2/backend/TASK-048-v3-report-contract`).
- Completed prerequisite decisions:
  - `TASK-047`: ADR-032 approved the v3 AI report policy/scope-lock and
    maintained prohibitions before implementation.
  - `TASK-048`: ADR-033 superseded ADR-032 for the final eight-field v3
    content/display contract.
- Current runtime state: `/api/issues/{id}/report` still serves the current v2
  report path. ADR-033 is approved documentation and has not yet been
  implemented in runtime code.
- No code, database schema, dependency, infrastructure, deployment, provider
  call, or database write is part of this PM allocation task.

## Approved v3 Contract

ADR-033 is the implementation source of truth. The content fields are:

1. `issue_overview`
2. `current_data_reading`
3. `possible_outlook`
4. `possible_drivers`
5. `external_context`
6. `what_to_check`
7. `data_limitations`
8. `caution_note`

`external_context` is the only nullable value. Its key remains required, and
the frontend hides that section only when the value is `null`.

## Work Allocation

| ID | Owner | Branch | Scope | Parallel? |
|----|-------|--------|-------|-----------|
| `TASK-049` | Data/AI Implementer | `data-ai/TASK-049-v3-report-generation` | Implement v3 generation, prompt-versioning, deterministic caution, non-causal context handling, and safety validation. | Yes |
| `TASK-050` | Backend Implementer | `backend/TASK-050-v3-report-runtime` | Implement the v3 report API/read contract, shared schema, and legacy-version exclusion. | Yes |
| `TASK-051` | Frontend Implementer | `frontend/TASK-051-v3-report-cards` | Implement dynamic ADR-033 section rendering with one visible card section at a time. | Yes |
| `TASK-053` | Reviewer | `review/TASK-053-v3-report-copy-lint` | Review integrated runtime, UI, response shape, copy safety, mobile behavior, and data-as-of/caution placement. | After integration |

## Parallelization Judgment

`TASK-049`, `TASK-050`, and `TASK-051` can begin at the same time because
ADR-033 freezes field names, nullability, labels, order, and safety boundaries.
The likely conflict surface is the shared report schema. To keep that clean,
`TASK-050` owns the Backend/Pydantic/API contract edits, while `TASK-049`
implements generation and validation against the documented contract and
rebases if shared schema changes land first.

`TASK-051` can build against ADR-033 without waiting for live v3 rows by using
typed fixture data and the documented `not_yet_generated` state. Its merge
should still wait for Backend contract compatibility evidence.

`TASK-053` is intentionally sequential. It should start after the three
implementation branches have reviewable integration evidence, because its job
is to catch cross-surface mismatches rather than isolated file-level issues.

## Merge / Review Order

1. `TASK-050` should land or provide a stable integration branch first if the
   shared API schema changes would otherwise cause duplicate edits.
2. `TASK-049` should follow with generation, prompt-version, and safety tests
   aligned to the Backend schema.
3. `TASK-051` can merge once the public response type is stable and the dynamic
   card UI passes responsive checks.
4. `TASK-053` performs the final integrated copy/contract review before any
   report refresh, screenshot capture, or deployment.

## Approval Gates

- The ADR-033 response-shape change is already approved by `TASK-047` and
  `TASK-048`.
- A real AI provider call or writing newly generated reports to the configured
  DB remains separately approval-gated.
- Deployment remains separately approval-gated.
- A database migration, new dependency, infrastructure change, or public route
  path change is not expected; if introduced, it requires separate approval.
- Automated news matching, individual wallet/participant/trader analysis, and
  action-oriented financial wording remain out of scope.

## Status

Day 5 v3 implementation is now assigned. Runtime remains v2 until
`TASK-049`, `TASK-050`, `TASK-051`, and `TASK-053` are completed and accepted.
