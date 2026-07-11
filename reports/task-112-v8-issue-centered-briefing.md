# TASK-112: V8 issue-centered briefing

Date: 2026-07-11  
Owner: Data/AI Implementer  
Branch: `data-ai/TASK-112-v8-issue-centered`  
Status: Implemented

## Outcome

The active on-demand writer and public report contract now use v8. V8 keeps
the existing opaque evidence bundle, source-parent linkage, accepted A-C source
records, cache fingerprint, append-only request/lease events, safe links,
last-known-good behavior, timestamps, caution, and prohibited-language filter.

The authored structure is issue-centered:

1. `current_situation`
2. `recent_change`
3. optional `interpretation`
4. optional `key_conditions`
5. optional `what_to_watch`
6. optional `limitations`

`current_situation` and `recent_change` are required and section types cannot
repeat. The summary is 100-500 characters and sections carry evidence refs at
section level. If an authored limitations section exists, the frontend omits
the separate deterministic limitations card to prevent repetition; caution
remains visible.

## Versioning

- prompt: `v8`
- policy: `v8-issue-centered-1`
- input schema: `v8-writer-input-1`
- public report: `report_version="v8"`

V7 prompt/models and stored rows remain intact. V8 reuses the existing JSONB
and request tables, so no migration was required.

## Scope

No provider call, database write, migration application, dependency,
infrastructure change, deployment, production action, or legacy deletion was
performed.
