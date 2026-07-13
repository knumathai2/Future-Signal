<!--
Purpose:        TASK-128 implementation and bounded evaluation record
Owner:          Data/AI / Backend Implementer
Update Trigger: Successful follow-up evaluation or scope correction
Harness Version: 1.1
-->

# TASK-128 — Tool-Free Scenario Writer

_Status: In progress — successful response awaits a separately approved call_

## Implemented

- Applied migration 006 only to the configured `ENV=local` database and
  verified six scenario tables plus 29 constraints.
- Added a non-agentic writer with no tools, browser, file, URL-fetch, database,
  or external-action capability inside the model call.
- Built the prompt from one reconstructed issue bundle, immutable premise
  classes, and bounded same-session turns; no capability or credential enters
  the prompt.
- Added strict JSON parsing, exact/current-turn premise refs, source-parent
  checks, assumption framing, prohibited-language, leakage, unsupported-number,
  restricted-Markdown, block, total-text, and program-budget gates.
- Added explicit PostgreSQL-safe turn → request → event insertion ordering.
- Added a guarded CLI that processes exactly one queued request.

## Bounded evaluations

- Provider/model: configured OpenRouter path / `openai/gpt-5.6-luna`
- Total input/output tokens: 2,704 / 1,397
- Total recorded cost: USD 0.0117605
- Provider results: HTTP 200 for both calls
- First product result: failed closed with `assumption_promotion`
- Second product result: failed closed with `unsupported_number`
- Persisted assistant turns: 0
- Persisted response blocks: 0
- Automatic retries: 0

The initial detector recognized `조건부 시나리오` and a narrow set of Korean
forms but did not cover all natural safe conditional-path wording. It now
accepts explicit `조건부`, `시나리오`, `경로`, `가정`, `전제`, and bounded
`경우` forms while the unframed fact-promotion regression remains blocked.
The second validator interpreted the hyphens in an ISO date as numeric minus
signs, so a natural Korean rendering of the same date failed. Numbers now use
canonical comparison across ISO and Korean date formatting while retaining
the sign of actual signed values and continuing to reject new values.

## Verification

```text
Focused scenario tests: 34 passed
Backend suite: 536 passed
Ruff: passed
git diff --check: passed
```

## Remaining gate

One additional provider call is required to produce and persist the requested
AI response. Both call authorizations are consumed, so that follow-up must
be explicitly approved. No other database, dependency, infrastructure,
Frontend, deployment, or production action is implied.
