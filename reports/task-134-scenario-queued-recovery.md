<!--
Purpose:        TASK-134 queued scenario recovery implementation and evidence
Owner:          Backend / Data-AI Implementer
Update Trigger: Recovery policy, pool bounds, or evaluation result changes
Harness Version: 1.1
-->

# TASK-134 — Attempt-zero scenario recovery

_Completed: 2026-07-13_

## Root cause

The latest user turn was stored, but its request remained `queued` at attempt
zero for more than ten minutes. No `scenario_worker` process remained and no
assistant turn or response block existed. A prior run had also observed the
Supabase session-mode 15-client ceiling while API and child-worker processes
used SQLAlchemy's effective 5+10 default pools.

## Implementation

- PostgreSQL pool defaults: three persistent, one overflow, ten-second timeout,
  and 300-second recycle; optional environment overrides remain tightly bounded.
- Recovery eligibility: only `queued`, attempt zero, at least five seconds old.
- Trigger: authenticated turn-status read or stored-block SSE loop.
- Spawn guard: process-local 20-second cooldown and maximum three launches.
- Provider guard: `SELECT ... FOR UPDATE` on the immutable request before the
  `running` event, so concurrent children cannot both call the provider.
- Exclusion: running, succeeded, and failed attempts never auto-recover.

## Verification

- Ruff passed.
- Focused DB/launcher/API/writer/model tests: 44 passed.
- Full Backend suite: 546 passed.
- After server restart, the original browser's authenticated connection moved
  the preserved request from queued attempt zero to running attempt one without
  a manual worker command.
- Exactly one OpenRouter call returned HTTP 200 and succeeded.

| Field | Result |
|---|---|
| Input/output tokens | 1,312 / 784 |
| Cost | USD 0.00634325 |
| Assistant turns | 1 |
| Validated blocks | 3 |
| Duplicate/retry calls | 0 |
| Pool-ceiling recurrence | 0 |

## Boundaries

No `.env` edit, dependency, schema, migration, other database, context research,
model tool, running-attempt recovery, second provider call, infrastructure or
deployment change, production write, default-feature activation, or TASK-131
transition occurred. Local Frontend and Backend servers remain running for the
user to verify the recovered response.
