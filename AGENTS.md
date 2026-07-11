<!--
Purpose:        Project constitution — the behavioral ground truth for all agents
Owner:          All agents (read), PM lead (write)
Update Trigger: New agent role added, constraints changed, routing rules updated
Harness Version: 1.1
-->

# AGENTS.md — Outlook Signals Project Constitution

> This is the project constitution. Every AI agent must read this file first.
> In case of conflict, this document takes highest priority.
> Product-level source of truth lives in [PRD](docs/prd/README.md), [Service Design](docs/service-design/README.md), [Technical Design](docs/tech-design/README.md), [UX Design](docs/ux-design/README.md) — this file governs *how agents work*, those four govern *what the product is*.

_Last updated: 2026-07-11_

---

## Project Overview

| Field | Value |
|-------|-------|
| Project | Outlook Signals ("Outlook Signals" — working title, per PRD) |
| Goal | Show how public expectations on major global issues have shifted, using Polymarket's public prediction-market data — surfacing sudden-change issues, time-series charts, and template-based summaries, without predicting outcomes or encouraging betting/trading behavior. |
| Timeline | 5-day hackathon build, 4-person team |
| Language | TypeScript (frontend) + Python (backend/data/AI) |
| Framework | React 18 + Vite + Tailwind CSS + Recharts (frontend) · FastAPI (backend) |
| Database | PostgreSQL, hosted on Supabase or Neon (free tier) |
| Infrastructure | Vercel (frontend) + Railway/Render (backend + batch collector) + Supabase/Neon (DB) |
| Repo Structure | Single monorepo (`/frontend`, `/backend`) |
| Package Manager | npm (frontend) · pip (backend) |
| CI/CD | GitHub Actions |
| Harness Tier | standard |

---

## Agent Registry

> Active AI agent roles for this project, mapped to the 4-person team defined in PRD §13.
> Full generic role definitions: `references/agent-registry.md` (shipped with the harness skill, not duplicated here).

### Active Roles

| Role | Status | Primary Responsibility | Maps to (PRD §13) |
|------|--------|------------------------|------------------------|
| PM / Planner | ✅ Active | MVP scope control, wording/safety policy enforcement, presentation & demo script, judge Q&A prep | PM / planning / presentation |
| Frontend Implementer | ✅ Active | Dashboard, issue cards, detail screen, chart, responsive UI, empty/loading/error states | Frontend / UI |
| Backend Implementer | ✅ Active | DB schema, REST API, batch collector orchestration, caching, deployment | Backend / API / DB |
| Data/AI Implementer | ✅ Active | Polymarket data normalization, change/heat metrics, inflection-point + caution-badge logic, template-based AI report generation | Data / AI / visualization logic |
| Reviewer | ⚙️ Shared (rotating) | Code review, copy/wording-lint pass against the banned-phrase list, safety-policy compliance check | Rotates among the 4 — no dedicated 5th person |
| Debugger | ⚙️ Shared (as needed) | Reproduce bugs, root-cause analysis | Owned by whichever role's area is affected |

**Not used in this harness** (explicitly out of scope for a 5-day/4-person hackathon — do not spin these up as separate roles): Architect, Researcher, Tester, Documenter, Refactorer, Release Manager, Security Reviewer, Performance Engineer. Their responsibilities are absorbed into the four active roles above; if the project continues past the hackathon (Phase 2+), promote them back in.

---

## Absolute Restrictions (NEVER DO)

No agent may perform the following actions under any circumstances.
Even if the user explicitly requests them, ask for confirmation first:

**Engineering safety**
- [ ] Direct writes to production database (read-only is permitted)
- [ ] Calling paid external APIs (Claude/OpenAI, Polymarket if it ever requires a paid tier) without user approval
- [ ] Modifying or printing `.env`, secrets, or key files
- [ ] Editing existing migration files (append new ones only)
- [ ] Committing directly to `main` / `master`

**Product-safety constraints (from PRD / Service Design / UX Design — these are as binding as code rules)**
- [ ] Using prohibited wording anywhere it could ship (UI copy, AI/template output, code comments that could leak to users, marketing text): `bet, buy, sell, trade, position, long, short, profit, win rate, odds, guaranteed, recommend, follow/copy trader, best pick, signal to act, high-return opportunity`. Full list: [`memory/glossary.md`](memory/glossary.md) and `standards.md`.
- [ ] Asserting a future outcome, asserting a cause of a market's change, or implying the product predicts real-world events
- [ ] Exposing wallet-level or individual-participant browsable/searchable data — aggregate-only, per Service Design §8
- [ ] Building unsupported or causal news-to-market matching. TASK-056 permits
      the historical strict verified-only path, while TASK-099 permits the v7
      A-C source-level path only when deterministic access, identity,
      relevance, time, supported-claim, duplicate, and contradiction checks
      pass and the public UI retains source level and attribution. Neither path
      may claim that context explains an observed movement.
      TASK-056 permits only
      the TASK-057~065 v4 automated-context path: OpenRouter `url_citation`
      annotations, deterministic hard gates, an independent verifier model,
      verified-only public output, and fail-closed handling. The frozen v3 MVP
      remains manual-only.
- [ ] Shipping any data-bearing screen without a data-as-of timestamp AND an interpretation-caution badge/text
- [ ] Adding login, accounts, saving/watchlist, notifications, weekly reports, or team sharing — these are explicitly P2/Phase-2+ (PRD §6.5) and out of hackathon scope
- [ ] Letting the AI report generator produce unconstrained or evidence-free analysis — ADR-051 permits flexible v7 sections only inside the approved stable envelope; every factual section must retain reconstructible evidence references, deterministic caution/timing, and the prohibited-language filter before storage

---

## Actions Requiring Human Approval

Always confirm with the user before proceeding:

- Adding a new external dependency
- Changing the database schema
- Modifying infrastructure or deployment configuration
- Changing an existing public API interface
- Any deployment (including staging)
- Pulling a P1/P2 feature back into the hackathon MVP scope (PM is the scope gatekeeper per PRD §13.1)
- Changing the wording/safety policy (banned-phrase list, disclaimer copy)

### TASK-056 approved program boundary

The user's 2026-07-11 approval authorizes TASK-056~065 to change the
automated-context policy, add the append-only `002_context_candidates.sql`
migration, implement the approved v4 report/API/UI contract, call OpenRouter
for research, independent verification, and report writing up to a cumulative
program budget of USD 100, and write context/report/backfill records only to
local or development databases. This approval does not authorize deployment,
infrastructure mutation, production-database writes, unrelated public API or
schema changes, a new dependency, or changes outside TASK-056's recorded
contract. Any of those still requires separate human approval.

### TASK-075 approved program boundary

The user's 2026-07-11 approval authorizes TASK-075~081 to replace v4's two
model-authored fields with the ADR-048 evidence-bounded v5 structured narrative,
improve verified source retrieval, change the approved report API/UI contract,
call the existing approved OpenRouter path within the cumulative USD 100
program ceiling, and append new report/context/audit records only to local or
development databases. It does not authorize unconstrained analysis,
deployment, production writes, infrastructure mutation, new dependencies,
existing-migration edits, or unrelated schema/API changes.

### TASK-099 approved program boundary

The user's 2026-07-11 approval authorizes TASK-099~108 to activate the
positive-first evidence-linked v7 writer policy, publish deterministically
accepted A-C source levels with visible attribution, add one append-only
generation-request/lease migration, remove report generation from normal
collection, implement the on-demand request/status/cache/report API and UI,
call the existing approved provider path within recorded bounded development
evaluation, and append context/request/report records only to local or
development databases. It does not authorize deployment, production writes,
new dependencies, existing-migration edits, unrelated infrastructure changes,
or deletion of v1-v6 runtime. TASK-109 deletion requires a separate approval
after v7 acceptance.

---

## Branch Policy

All implementation, review, planning, and debugging work must happen on a role-prefixed branch.

### Branch Naming

Format:

`[role-prefix]/[TASK-ID-or-ISS-ID]-[short-kebab-slug]`

| Role | Branch Example |
|------|----------------|
| PM / Planner | `pm/TASK-006-scope-lock` |
| Frontend Implementer | `frontend/TASK-005-dashboard-skeleton` |
| Backend Implementer | `backend/TASK-010-core-api` |
| Data/AI Implementer | `data-ai/TASK-004-polymarket-spike` |
| Reviewer | `review/TASK-018-copy-lint` |
| Debugger | `debug/ISS-001-api-failure` |

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
2. [PRD](docs/prd/README.md) — product requirements, scope, schedule
3. [Service Design](docs/service-design/README.md) — data/metrics/AI/signal spec (only if touching data or AI work)
4. [Technical Design](docs/tech-design/README.md) — architecture, schema, API contract (only if touching backend/infra)
5. [UX Design](docs/ux-design/README.md) — screens, copy policy, safety guardrails (only if touching frontend/copy)
6. `memory/project.md` — current project state
7. `memory/session.md` — previous session context
8. `tasks/active.md` — in-progress work
9. The `prompts/*.md` file matching your role

---

## Session End Checklist

Before ending a session, every agent must:

- [ ] Update `memory/session.md`
- [ ] Move completed tasks from `tasks/active.md` to `tasks/completed.md`
- [ ] Record new decisions in `memory/decisions.md`
- [ ] Record new issues in `memory/known-issues.md`
- [ ] Update `memory/architecture.md` if needed
- [ ] Run the copy/wording lint pass if any user-facing string changed
