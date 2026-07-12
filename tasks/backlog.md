<!--
Purpose:        Prioritized list of tasks not yet started
Owner:          PM / Planner
Update Trigger: New task added or priority changed
Harness Version: 1.1
-->

# Backlog — Outlook Signals

_Last updated: 2026-07-12_
_Current assignments live in `tasks/active.md`; completed work lives in `tasks/completed.md`._

## Release and Presentation

| ID | Task | Owner | Resume condition |
|----|------|-------|------------------|
| TASK-020 | Deploy the approved service set | Backend Implementer | Explicit deployment approval and target-platform access |
| TASK-021 | Finalize presentation assets, rehearse the demo, and capture the backup sequence | PM | Presentation work resumes |

## Reliability Items

| ID | Task | Owner | Resume condition |
|----|------|-------|------------------|
| ISS-017 | Recover queued requests that outlive a worker process | Backend Implementer | Recovery behavior is approved for implementation |
| ISS-018 | Evaluate cited-source compatibility with the active writer | Data/AI Implementer | A new bounded provider evaluation is approved |

## Summary and Scenario Chat — Phase 2 Proposal

TASK-123~125 record the plan, approved next-contract policy, and approval-ready
threat/API/storage proposal. The rows below are not authorized implementation
work. They enter active work only after their stated scope and approval gates
are satisfied.

| ID | Task | Owner | Resume condition |
|----|------|-------|------------------|
| TASK-127 | Implement a feature-flagged relaxed summary writer and validator | Data/AI Implementer | TASK-124 approval; provider evaluation remains separately gated |
| TASK-128 | Implement the tool-free scenario writer and premise-state validation | Data/AI / Backend | TASK-125~127 complete; provider budget separately approved |
| TASK-129 | Build the isolated scenario conversation UI and safe renderer | Frontend Implementer | Public API approved and TASK-128 fixtures available |
| TASK-130 | Run security red-team and bounded local/development evaluation | Reviewer | Explicit provider-call and any local migration approval |
| TASK-131 | Decide activation, rollback period, and v8 transition | PM / Reviewer | TASK-130 evidence reviewed and human activation approval received |

## Maintenance

| ID | Task | Owner | Approval note |
|----|------|-------|---------------|
| TD-001 | Lazy-load the chart bundle | Frontend Implementer | No external approval unless a dependency changes |
| TD-002 | Upgrade Vite | Frontend Implementer | Dependency approval required |
| TD-003 | Declare the minimum supported Python version | Backend Implementer | Confirm hosting-runtime compatibility |
| TD-007 | Normalize remaining API error payloads | Backend Implementer | Public API approval may be required |
| TD-009 | Localize remaining fallback strings | Frontend Implementer | Run wording-policy validation |
| TD-012 | Upgrade GitHub Actions majors | Backend Implementer | Infrastructure approval required |

## Superseded Planning Detail

The original Day 1–5 allocation notes and the proposed TASK-066~074 v4
stretch sequence were absorbed by completed TASK-075~117 work. Their historical
text remains recoverable from Git and is not an active execution plan.

The binding historical v4 approval packet that must remain auditable is
`reports/task-055-automated-context-execution-plan.md`.
