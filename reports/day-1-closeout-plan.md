# Day 1 Closeout Plan — Outlook Signals

_Date: 2026-07-08_
_Owner: PM / Planner_
_Purpose: Day 1 작업을 "완료"로 닫기 위해 남은 리뷰/승인 항목을 정리하고 closeout 결과를 기록한다._

## Summary

Day 1 implementation work is closed. The remaining items identified for closeout were review/approval decisions, not new feature implementation. They are now resolved so the team can enter Day 2 without building on unresolved drafts.

## Closeout Results

| ID | Remaining work | Owner | Decision/output | Status |
|---|---|---|---|---|
| D1-CLOSE-001 | `TASK-003` API contract PM/Frontend sign-off | PM + Frontend + Backend | Accepted. Public route/field names are safe for Day 2 implementation dependency. `200 {"status": "not_yet_generated"}` is accepted as the report-empty response in ADR-008. | closed |
| D1-CLOSE-002 | `TASK-002` DB schema draft closeout | PM + Backend | Accepted as a Day 1 draft artifact, explicitly unapplied. Applying it to any shared or production DB still needs separate human approval. Recorded in ADR-011. | closed |
| D1-CLOSE-003 | Task board alignment after the two decisions | PM | `TASK-002` and `TASK-003` moved to `tasks/completed.md`; `tasks/active.md` has no remaining Day 1 tasks. | closed |

## Should Resolve Before Starting Day 2 Integration

| ID | Work | Why it matters | Suggested handling |
|---|---|---|---|
| D1-BRIDGE-001 | Frontend dummy issue shape vs. API response shape reconciliation | Prevents Day 2 integration churn when replacing dummy data. | Treat as first step of `TASK-010`/frontend integration, not a new Day 1 feature. |
| D1-BRIDGE-002 | Python runtime minimum | Default Python 3.9 failed local backend dependency install; Python 3.11 passed. | Keep README guidance now; decide later whether to formalize a backend Python version in tooling. |
| D1-BRIDGE-003 | Static fallback path naming | Demo fallback is required later, but current dummy data already proves a local fallback shape. | Resolve during Day 2–4 fallback work, not as a Day 1 blocker. |

## Explicitly Not Day 1 Closeout

These are expected Day 2+ implementation tasks and should not delay Day 1 closure:

- Batch collector fetch/normalize work (`TASK-007`)
- Snapshot + metrics persistence (`TASK-008`)
- ±5pp signal detection implementation (`TASK-009`)
- Real data-backed API routes (`TASK-010`)
- Template report generation and banned-phrase filter (`TASK-015`)

## Closeout Order Completed

1. PM reviewed `backend/API_CONTRACT.md` and accepted ADR-008.
2. Backend/PM schema draft closeout recorded through ADR-011.
3. `tasks/active.md` and `tasks/completed.md` were updated.
4. Day 2 work can start from `TASK-007`, `TASK-008`, and `TASK-010`.
