<!--
Purpose:        TASK-132 auto-worker and bounded evaluation record
Owner:          Backend / Data-AI Implementer
Update Trigger: Scenario launcher or evaluation status changes
Harness Version: 1.1
-->

# TASK-132 — Scenario auto-worker and local evaluation

_Completed: 2026-07-13_

## Outcome

New scenario turns now start the existing guarded worker automatically only in
local/development after the immutable request commits. The API process does not
construct a provider client, and idempotent replay does not spawn a duplicate.

## Evaluation

- Provider/model: OpenRouter / `openai/gpt-5.6-luna`
- Calls authorized: exactly one
- Calls consumed: exactly one
- Input/output: 1,141 / 744 tokens
- Cost: USD 0.0058895
- Terminal state: `failed`
- Safe error: `unsupported_number`
- Stored assistant turns/blocks: zero / zero
- Automatic retry: none

The provider returned HTTP 200. The complete response was rejected before
assistant-content persistence. Raw provider output was not stored or logged.

## Follow-up correction

The writer allowed ordered Markdown lists but previously scanned list markers
such as `1.` and `2.` as factual numbers. Writer version 2 now runs the strict
Markdown block parser first and compares evidence only with paragraph text and
list-item content. Ordered indices are presentation metadata; any number inside
the actual prose or item remains evidence-gated. A regression proves ordered
markers pass while the existing unsupported-number case remains blocked.

The Frontend now removes the failed current turn and displays a generic safe
failure notice without exposing validation internals.

## Verification

- Ruff passed.
- Full Backend suite: 542 passed.
- Frontend Prettier, typecheck, lint, production build, and scenario parser
  regression passed.
- Browser verified session creation, automatic transition through the worker,
  SSE failure completion, removal of the failed current turn, and retention of
  the existing session. Static Frontend checks cover the subsequently added
  generic failure notice.

## Boundaries

No second provider call, `.env` edit, context research, model tool, dependency,
schema, migration, other database, infrastructure, deployment, production
write, default-feature activation, or TASK-131 transition occurred.

## Subsequent status

TASK-133 later consumed a separately approved post-fix call and stored the
first validated writer-v2 scenario response. TASK-132's recorded failed call
and cost remain unchanged audit history.
