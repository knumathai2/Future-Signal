<!--
Purpose:        Project constitution — the behavioral ground truth for all agents
Owner:          All agents (read), PM lead (write)
Update Trigger: New agent role added, constraints changed, routing rules updated
Harness Version: 1.1
-->

# AGENTS.md — Outlook AI Signals Project Constitution

> This is the project constitution. Every AI agent must read this file first.
> In case of conflict, this document takes highest priority.
> Product-level source of truth lives in [PRD](docs/prd/README.md), [Service Design](docs/service-design/README.md), [Technical Design](docs/tech-design/README.md), [UX Design](docs/ux-design/README.md) — this file governs _how agents work_, those four govern _what the product is_.

_Last updated: 2026-07-13_

---

## Operational Quick Reference

1. Read the required context in [Context Loading Order](#context-loading-order).
2. Work only on a compliant role-prefixed maintenance branch.
3. Check [Absolute Restrictions](#absolute-restrictions-never-do) and
   [Actions Requiring Human Approval](#actions-requiring-human-approval)
   before changing code, data, contracts, infrastructure, or user-facing copy.
4. Treat every recorded approval as task-, environment-, and action-specific;
   consumed approval does not authorize another call, write, migration, or
   deployment.
5. Complete the [Maintenance Handoff Checklist](#maintenance-handoff-checklist)
   before handoff.

## Contents

- [Project Overview](#project-overview)
- [Absolute Restrictions](#absolute-restrictions-never-do)
- [Actions Requiring Human Approval](#actions-requiring-human-approval)
- [Branch Policy](#branch-policy)
- [Context Loading Order](#context-loading-order)
- [Maintenance Handoff Checklist](#maintenance-handoff-checklist)

---

## Project Overview

| Field       | Value                                                                                                                                     |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Project     | Outlook AI Signals                                                                                                                        |
| Goal        | Show changes in reflected public expectations from aggregate Polymarket data without predicting outcomes or encouraging financial action. |
| Application | React 18 + Vite + TypeScript frontend; FastAPI + Python backend and workers                                                               |
| Data        | PostgreSQL with append-only market, evidence, report, and scenario records                                                                |
| Deployment  | Docker Compose and Caddy on the configured VPS                                                                                            |
| Automation  | GitHub Actions market-data collection every four hours                                                                                    |

---

## Absolute Restrictions (NEVER DO)

No agent may perform the following actions under any circumstances.
Even if the user explicitly requests them, ask for confirmation first:

### Engineering safety

- Direct writes to production database (read-only is permitted)
- Calling paid external APIs (Claude/OpenAI, Polymarket if it ever requires a
  paid tier) without user approval
- Modifying or printing `.env`, secrets, or key files
- Editing existing migration files (append new ones only)
- Committing directly to `main` / `master`

### Product safety

These constraints come from the PRD, Service Design, and UX Design and are as
binding as code rules.

- Using hard-block wording anywhere it could ship (UI copy, AI/template output,
  code comments that could leak to users, marketing text): `bet`, `buy`, `sell`,
  `trade`, `position`, `long`, `short`, `profit`, `win rate`, `odds`,
  `follow/copy trader`, `best pick`, `signal to act`, and
  `high-return opportunity`. Contextual certainty,
  guarantee, institutional recommendation, procedural opportunity, attributed
  outlook, and attributed cause may ship only under deterministic
  negation/inquiry or exact source-support plus attribution rules. Full policy:
  [`memory/glossary.md`](memory/glossary.md) and `standards.md`.
- Asserting a future outcome, asserting a cause of a market's change, or
  implying the product predicts real-world events
- Exposing wallet-level or individual-participant browsable/searchable data —
  aggregate-only, per Service Design §8
- Building unsupported or causal news-to-market matching. Current automated
  context requires OpenRouter `url_citation` annotations, deterministic access,
  identity, relevance, timing, supported-claim, duplicate and contradiction
  checks, independent verification, and visible attribution. It may not claim
  that context explains an observed movement.
- Shipping any data-bearing screen without a data-as-of timestamp AND an
  interpretation-caution badge/text
- Adding login, accounts, saving/watchlist, notifications, weekly reports, or
  team sharing — these remain outside the implemented product scope
- Letting the AI report generator produce unconstrained or evidence-free
  analysis — flexible v8 sections are permitted only inside the approved stable
  envelope; every factual section must retain reconstructible evidence
  references, deterministic caution/timing, and the prohibited-language filter
  before storage

---

## Actions Requiring Human Approval

Always confirm with the user before proceeding:

- Adding a new external dependency
- Changing the database schema
- Modifying infrastructure or deployment configuration
- Changing an existing public API interface
- Any deployment (including staging)
- Expanding the product into an excluded or deferred feature area
- Changing the wording/safety policy (banned-phrase list, disclaimer copy)

### Historical approval records

Task-specific approvals and consumed authorization records belong in
`memory/decisions.md`, `tasks/completed.md`, and Git history. Historical
approval does not authorize a new call, write, migration, deployment, policy
change, or other gated action.

---

## Branch Policy

All implementation, review, planning, and debugging work must happen on a role-prefixed branch.

### Branch Naming

Format:

`[role-prefix]/[TASK-ID-or-ISS-ID]-[short-kebab-slug]`

| Role                 | Branch Example                         |
| -------------------- | -------------------------------------- |
| PM / Planner         | `pm/TASK-006-scope-lock`               |
| Frontend Implementer | `frontend/TASK-005-dashboard-skeleton` |
| Backend Implementer  | `backend/TASK-010-core-api`            |
| Data/AI Implementer  | `data-ai/TASK-004-polymarket-spike`    |
| Reviewer             | `review/TASK-018-copy-lint`            |
| Debugger             | `debug/ISS-001-api-failure`            |

Rules:

- Every branch must start with the owning role prefix.
- Every branch must include the related `TASK-ID` or `ISS-ID`.
- The final slug must be short, descriptive, and kebab-case.
- Do not commit directly to `main` or `master`.
- Merge into `main` or `master` only through the project review flow and required human approval gates.

---

## Context Loading Order

At the start of every session, read these files in order:

1. `AGENTS.md` (this file) — confirm the rules
2. `README.md` and `memory/project.md` — final product and operating state
3. `memory/architecture.md` — implemented runtime boundaries and invariants
4. [PRD](docs/prd/README.md) — product requirements and scope
5. [Service Design](docs/service-design/README.md) — only for data or AI work
6. [Technical Design](docs/tech-design/README.md) and
   `backend/API_CONTRACT.md` — only for backend, schema, API, or infrastructure
7. [UX Design](docs/ux-design/README.md), `standards.md`, and
   `memory/glossary.md` — only for frontend, copy, or safety work

---

## Maintenance Handoff Checklist

Before ending maintenance work:

- [ ] Update `memory/project.md` when final operating state changes
- [ ] Update architecture, API, or design documents when behavior changes
- [ ] Record lasting decisions in `memory/decisions.md`
- [ ] Add a concise audit row to `tasks/completed.md` when useful
- [ ] Run the copy/wording lint pass if any user-facing string changed
- [ ] Verify local Markdown links and run `git diff --check`
