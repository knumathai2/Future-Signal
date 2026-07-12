<!--
Purpose:        Active bugs, technical debt, and data limitations
Owner:          Debugger / Reviewer
Update Trigger: New issue, resolution, or priority change
Harness Version: 1.1
-->

# Known Issues — Outlook Signals

_Last updated: 2026-07-12_

Resolved forensic history remains available in Git, `memory/decisions.md`, and
`tasks/completed.md`. This file contains only current action items and durable
data limitations.

## Active bugs

| ID | Severity | Description | Next action |
|---|---|---|---|
| ISS-017 | Medium | A queued on-demand request can remain without a worker after process loss. Expired running leases recover, but every orphaned queued state is not yet reclaimed automatically. | Design a bounded startup or poll-time recovery path without changing immutable request identity. |
| ISS-018 | Medium | The configured v8 research model may return no standard citation annotations. The workflow fails safely to a zero-source state, but source yield is limited. | Evaluate provider-compatible annotation handling under a new bounded approval; do not weaken URL/source-parent checks. |

## Technical debt

| ID | Description | Impact | Next action |
|---|---|---|---|
| TD-001 | Frontend production build reports a chunk larger than 500kB, primarily from the chart bundle. | Non-blocking initial-load cost. | Consider route-level lazy loading in a separately scoped Frontend task. |
| TD-002 | The approved Vite 5.x range retains development-server audit findings. | Local development exposure; a major upgrade needs approval and full UI retest. | Review a dependency-maintenance proposal before changing versions. |
| TD-003 | The pinned Backend driver is unreliable on the machine's default Python 3.9 runtime. | New contributors may fail during setup. | Continue documenting Python 3.11; formalize the minimum version only in an approved tooling task. |
| TD-007 | Invalid issue-list enum parameters use FastAPI's current 422 response rather than the original 400 plan. | Low contract inconsistency. | Keep documented behavior unless a public API change is separately approved. |
| TD-009 | Static Backend fallback issue titles may be English while the primary Frontend presentation is Korean. | Language inconsistency during fallback use. | Localize only through a reviewed copy task without changing timing/caution behavior. |
| TD-012 | GitHub Actions reports an action-runtime compatibility warning. | Non-blocking workflow maintenance risk. | Review current official action releases under infrastructure approval. |

## Durable data limitations

- CLOB history can be sparse or irregular for low-activity markets.
- Volume represents aggregate notional activity, not a count of people.
- Wallet-level or individual-participant exploration is excluded.
- A reflected expectation value is not a real-world result probability.
- Time proximity between an external source and a data movement does not prove
  a relationship.

## Recently closed

- **ISS-020**: public source validation now rejects local/private targets,
  public IPv6 canonicalization preserves brackets, exact stored source links
  remain unchanged in the Frontend, invalid detail tabs normalize to overview,
  and report-read issue IDs use consistent path encoding.
- **ISS-019**: issue-list re-search now preserves Korean IME composition by
  keeping a local draft and deferring URL synchronization until composition
  ends.
- **ISS-016**: superseded by the accepted v8 on-demand path and successful
  stored/API/UI reconstruction.
- **TD-011**: obsolete stored v1-v7 report rows were removed from the approved
  local development database; active v8 rows remain.

## Issue template

```text
### ISS-XXX: Brief description
- Severity:
- Found:
- Owner:
- Reproduction:
- Expected:
- Actual:
- Safety or data impact:
- Proposed next action:
```
