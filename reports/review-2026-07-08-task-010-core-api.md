# Review Report — TASK-010 Core Read API

_Date: 2026-07-08_
_Reviewer role: Reviewer_
_Target: PR #10 / `backend/TASK-010-core-api`_

## Verdict

Approved after follow-up.

## Findings

1. **Fixed during review: auxiliary live reads could bypass the fallback path.**
   After `_resolve_live()` succeeded, `/api/issues/{id}` still queried
   `issue_signals` and `related_events`, and `/api/issues/{id}/history` still
   queried `market_snapshots` outside the guarded fallback path. A late DB
   failure or partial local schema could therefore produce a 500 even though
   the route-level fallback policy said live query failures should degrade.
   The reviewer follow-up now catches those `SQLAlchemyError`s: detail keeps
   the core issue and returns empty `signals`/`related_events`, while history
   returns the latest snapshot point already loaded for the issue.

2. **Resolved after review: ADR-013 confirmation recorded.**
   The PR documents `200` + static fallback instead of Technical Design §5's
   `503` fallback note. The response shape is unchanged, but this is still a
   public API behavior decision. The 2026-07-08 follow-up records the required
   user/PM-gate confirmation in ADR-013, so the previous Request Changes
   blocker is resolved.

## Verification

- `cd backend && .venv/bin/python -m pytest` → 19 passed
- `cd backend && .venv/bin/python -m ruff check .` → passed
- GitHub reports no configured checks for PR #10.

## Safety Review

- No writes to production/shared DB were performed.
- No external paid APIs were called.
- No migration files were edited.
- User-facing API paths remain under `issues`, `signals`, `reports`, and
  `categories`.
- Data responses still include `data_as_of` and `confidence_level`.

## Follow-Up

- 2026-07-08: ADR-013 confirmation recorded in `memory/decisions.md`; PR #10
  can move from Request Changes to approval if validation remains green.
