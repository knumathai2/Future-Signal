<!--
Purpose:        TASK-129 implementation and verification record
Owner:          Frontend Implementer
Update Trigger: Scenario UI contract or verification changes
Harness Version: 1.1
-->

# TASK-129 — Scenario conversation UI and safe renderer

_Completed: 2026-07-13_

## Outcome

The issue detail now has a fifth `시나리오 대화` tab, separate from the active
v8 briefing. The tab supports the approved anonymous 24-hour session lifecycle,
while the server feature remains default-off and production activation remains
outside this task.

## Implemented

- Capability storage in memory and sessionStorage only; no URL, analytics, or
  user-visible error exposure.
- Strict parsers for create/read/turn/status/SSE payloads with exact keys,
  timestamp, UUID, limit, and stream-path checks.
- Authenticated fetch-SSE with `Last-Event-ID`, bounded reconnect, block
  deduplication, and polling fallback.
- Inert paragraph and ordered/unordered-list rendering; HTML, headings, links,
  images, code, quotes, and table-like input fail closed.
- Idle, loading, unavailable, ready, queued/running, failure, stale, expired,
  limit, rate, recovery, and owner-deletion states.
- Visible premise classes, data-as-of time, caution, expiry, remaining turns,
  1,000-character input count, IME-safe Enter behavior, and fixed 44px controls.

## Verification

- Frontend: Prettier, typecheck, ESLint, production build, API URL regression,
  v8 report parser regression, and scenario parser/renderer regression passed.
- Backend compatibility: Ruff and 34 focused scenario API/writer/model tests
  passed.
- Browser: verified the five-tab contract, default-off unavailable state,
  actual local session creation, queued user turn and input lock, same-tab
  recovery, owner deletion, Arrow-key navigation, 320px width without page
  overflow, and minimum 44px visible controls.
- The browser console contained one expected history-fetch error only during the
  deliberate local backend restart between default-off and enabled QA. No UI
  exception occurred in the stable flows.

## Boundaries

No provider call, new dependency, schema change, migration action, deployment,
infrastructure change, production write, wording-policy change, or active-v8/
TASK-131 transition occurred. The temporary local session and queued turn used
for QA were owner-deleted before completion.
