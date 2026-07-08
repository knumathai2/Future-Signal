<!--
Purpose:        Key technical decision history in ADR format
Owner:          PM / Backend Implementer
Update Trigger: Record immediately after any significant technical or scope decision
Harness Version: 1.1
-->

# Decision Log — Outlook Signals

_Last updated: 2026-07-08_

## Template

```
### ADR-NNN: [Decision Title]
- **Date**: YYYY-MM-DD
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Decided by**: [Role / User]

**Context**: Why was this decision needed?
**Decision**: What was chosen?
**Rationale**: Why was this chosen?
**Trade-offs**: What are the downsides?
**Consequences**: What changed as a result?
```

---

### ADR-001: AI Development Harness v1.1 Adoption

- **Date**: 2026-07-07
- **Status**: Accepted
- **Decided by**: User

**Context**: A 4-person, 5-day hackathon team needs consistent context handoff between people/sessions and a shared scope-control mechanism.
**Decision**: Adopt AI Development Harness v1.1 (Standard tier) to structure agent roles, workflows, and memory.
**Rationale**: Eliminates context loss between sessions; gives the PM a concrete scope-gate mechanism (roadmap.md P0/P1/P2 tables) against the "trying to build everything at once" risk already flagged in PRD §15.1.
**Trade-offs**: Upfront documentation overhead on Day 1, when time is scarcest.
**Consequences**: All 4 roles operate from a shared, consistent context; PM enforces scope via `roadmap.md` and `AGENTS.md`.

---

### ADR-002: MVP scope narrowed to "sudden-change issue monitoring" (from broader "global issue outlook platform")

- **Date**: 2026-07-07 (recorded in PRD v1.1)
- **Status**: Accepted
- **Decided by**: PM / User

**Context**: The earlier PRD concept was too broad for 5 days / 4 people.
**Decision**: Fix the core experience to "check today's most-changed issues → detail chart → template summary + caution notice"; limit to 30–50 binary markets; template-based AI only; 3–5 manually-curated related events; exclude saving/notifications/reports/sharing/chart-export.
**Rationale**: A narrow, fully-working demo beats a broad, half-working one for hackathon judging (PRD §1.4, §15.5).
**Trade-offs**: Cuts real product features (personalization, saved issues, weekly reports) that have genuine user value — deferred to Phase 2/3.
**Consequences**: PRD §6.3–6.5 P0/P1/P2 tables are the binding scope contract; any request to add P2 features requires HUMAN APPROVAL per `AGENTS.md`.

---

### ADR-003: Template-constrained AI output only, never free-form analysis

- **Date**: 2026-07-07 (Service Design §6, Technical Design §10)
- **Status**: Accepted
- **Decided by**: PM / Data-AI Implementer

**Context**: Free-form LLM analysis on financial/prediction-market data carries high risk of causal assertions, overstated confidence, or advice-like language.
**Decision**: LLM is used only to fill fixed template slots (issue_summary, movement_explanation, key_change_context, uncertainty_summary, neutral_conclusion); every output passes a banned-phrase filter before storage; failed generations discard and keep the previous report live rather than auto-retrying.
**Rationale**: Keeps token cost predictable, keeps legal/ethical exposure low, matches the product's "not a prediction service" positioning (PRD §15.3, §15.4).
**Trade-offs**: Less rich/flexible output than a free-form analyst LLM would produce.
**Consequences**: All future AI output types must pass through the same filter before ship (Service Design §6, standing rule).

---

### ADR-004: Monorepo, npm + pip, GitHub Actions

- **Date**: 2026-07-07
- **Status**: Accepted
- **Decided by**: User (via harness setup interview)

**Context**: Technical Design left repo structure, package manager, and CI/CD undecided.
**Decision**: Single monorepo (`/frontend`, `/backend`); npm for frontend, pip for backend; GitHub Actions for the batch-collector schedule and basic lint/test.
**Rationale**: Minimizes cross-repo coordination overhead for a 4-person/5-day build; npm/pip are the zero-setup defaults for their respective ecosystems.
**Trade-offs**: Frontend and backend deploy to different platforms (Vercel vs Railway/Render) despite sharing a repo — requires each platform's build config to target the correct subfolder.
**Consequences**: `commands.md` and `tech-stack.md` assume this layout; Day 1 setup must configure both platforms' root-directory settings accordingly.

---

### ADR-005: Role-prefixed task branches and active-task assignment format

- **Date**: 2026-07-07
- **Status**: Accepted
- **Decided by**: User / PM

**Context**: The harness expects the PM to organize scope and route work to each role, but task selection and branch setup were still manual and easy to drift from.
**Decision**: Add a role-prefixed branch policy, require `Owner`, `Assignee`, `Branch`, and fixed `Status` values in `tasks/active.md`, and document preview-only automation script designs for assignment/start-task flows.
**Rationale**: Keeps role ownership, task IDs, and branch names aligned before implementation starts, while preserving human approval for file writes and git operations.
**Trade-offs**: Adds a small process step before coding starts.
**Consequences**: Agents must choose only assigned work from `tasks/active.md`, confirm the listed branch before starting, and never commit directly to `main` or `master`.

---

### ADR-006: Day 1 active work limited to P0 kickoff tasks

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 1 needed role-by-role assignment without expanding hackathon scope or blocking frontend work on backend/data availability.
**Decision**: Move `TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005`, `TASK-006`, and `TASK-011` into `tasks/active.md`; keep `TASK-007` in backlog until the Polymarket field/rate-limit spike validates the data shape.
**Rationale**: These tasks map directly to PRD §14 Day 1 deliverables: screen structure, API contract, sample data, scope lock, and presentation key messages.
**Trade-offs**: Backend has several small Day 1 tasks, so sequencing matters: scaffold and health endpoint first, then contract/schema draft.
**Consequences**: Each role has a concrete branch and Day 1 Definition of Done; schema application remains behind the human-approval gate in `AGENTS.md`.

---

### ADR-007: Backend Day 1 scaffold — Postgres driver, env loading, migration tooling

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: User (via human approval) / Backend Implementer

**Context**: `dependencies.md` pre-approved SQLAlchemy as the ORM but not a concrete Postgres driver package, and did not cover local `.env` loading or a migration-file format. TASK-001/TASK-002 needed these to produce a runnable scaffold and schema draft.
**Decision**: Use `psycopg[binary]` (psycopg3) as the Postgres driver and `python-dotenv` for local-dev `.env` loading only (both human-approved 2026-07-08, recorded in `dependencies.md`). Write the TASK-002 schema draft as plain SQL (`backend/migrations/001_initial_schema.sql`) rather than adopting a migration framework (e.g. Alembic), since the migration-tool choice is still an open Day 1 decision per `commands.md` and adopting one is a separate dependency decision from drafting the schema itself.
**Rationale**: Keeps the scaffold unblocked without pre-empting the still-open migration-tool decision; psycopg3 is actively maintained and works with both sync and future async SQLAlchemy engines.
**Trade-offs**: `commands.md`'s example commands (`alembic upgrade head`) don't match the current migration mechanism (`psql -f migrations/001_initial_schema.sql`) until the tool decision is made — flagged, not yet reconciled.
**Consequences**: `backend/migrations/001_initial_schema.sql` and the mirrored SQLAlchemy models in `backend/app/db/models.py` are draft-only and unapplied; applying them to any database still requires a separate human-approval step per `AGENTS.md`.

---

### ADR-008: `/api/issues/:id/report` not-yet-generated response uses 200, not 204

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Frontend Implementer / Backend Implementer

**Context**: Technical Design §5 specifies returning HTTP `204` with a JSON body hint `{"status": "not_yet_generated"}` when no AI report exists yet for an issue. HTTP `204 No Content` cannot carry a response body per spec — most clients discard it, so the frontend would never see the hint.
**Decision**: TASK-003's draft contract (`backend/API_CONTRACT.md`) instead returns `200 OK` with `{"status": "not_yet_generated"}`, keeping the same neutral-empty-state intent without the invalid HTTP semantics.
**Rationale**: Preserves the product intent (no error state; frontend shows a neutral placeholder) while fixing a factual protocol error in the source spec.
**Trade-offs**: Diverges from the literal Technical Design wording, so Technical Design §5 should be interpreted through this ADR for the report-empty response.
**Consequences**: Day 2 frontend/backend integration should treat `200 OK` with `{"status": "not_yet_generated"}` as the canonical no-report-yet response. If this ever changes, update `backend/API_CONTRACT.md`, `backend/app/schemas/issues.py::ReportNotYetGenerated`, and the corresponding route/tests together.

---

### ADR-011: Day 1 DB schema draft accepted, unapplied

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Backend Implementer

**Context**: Day 1 required a database schema artifact so Day 2 data pipeline and read API work can align on table boundaries, but `AGENTS.md` requires human approval before applying schema changes to any shared or production database.
**Decision**: Accept `backend/migrations/001_initial_schema.sql` and `backend/app/db/models.py` as the Day 1 schema draft artifact. The schema remains unapplied; applying it to any shared or production database is a separate approval-gated action.
**Rationale**: The draft includes the required MVP tables, preserves the append-only snapshot/metric strategy, and does not introduce `users`, `watchlists`, wallet-level, or participant-level tables.
**Trade-offs**: The schema has not yet been validated against a live hosted Postgres instance, and the migration-tool choice remains plain SQL for now rather than Alembic.
**Consequences**: `TASK-002` can close as "draft accepted, unapplied." Day 2 implementation may align to the draft shape, but any future schema correction must respect the project rule to append new migration changes rather than editing applied migration history.

---

### ADR-012: Day 2 active work limited to P0 data path, core API, and dashboard integration

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 1 closed with a working frontend dummy flow, accepted mock API contract, accepted-unapplied schema draft, and validated Polymarket field samples. The next risk is spreading Day 2 effort across attractive P1 work before the real data path reaches the dashboard.
**Decision**: Complete `TASK-031` for Day 2 allocation, then assign Day 2 active implementation work to `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`, and `TASK-012` only. Keep category filtering, `/api/signals` feed, volatility/attention metrics, report generation, event candidates, deployment, and copy-polish passes deferred until the P0 data/API/dashboard path is usable.
**Rationale**: This matches PRD §14's Day 2 deliverables: dashboard v1, ranking API, change-calculation data, and candidate issue list for the demo. It also preserves the PRD §13.1 operating principle that frontend, backend, and data work can proceed in parallel as long as the contract and handoff order stay explicit.
**Trade-offs**: Some visible polish and richer metrics remain idle even if they would improve the demo surface. The team may need a follow-up Day 2/3 bridge if live metric data arrives late.
**Consequences**: `tasks/active.md` is the Day 2 source of execution truth for implementation, `tasks/completed.md` records `TASK-031`, `tasks/backlog.md` no longer lists the moved Day 2 tasks, and `reports/day-2-work-allocation.md` records the sequence. Applying the schema draft to any shared or production database remains a separate human-approval gate.

---

### ADR-009: TASK-005 frontend uses local state and dummy issue contract

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Frontend Implementer

**Context**: The frontend needed a usable dashboard/detail flow before the backend API is ready.
**Decision**: Implement dashboard-to-detail navigation with React local state and a typed dummy issue data contract under `frontend/src/data`.
**Rationale**: This matches the Day 1 instruction to proceed without waiting for the API and avoids adding a router dependency.
**Trade-offs**: Browser URL state is not shareable yet; the API integration pass will need to replace the dummy source.
**Consequences**: Frontend and backend can align on the `Issue` shape while preserving the P0 demo flow.

---

### ADR-010: PR #6 audit risk is temporarily accepted without a Vite major upgrade

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: User / Frontend Implementer

**Context**: PR #6 originally cleared `npm audit` by moving the frontend build stack to Vite 8, but that crossed a major-version boundary and triggered the `dependencies.md` approval gate. Reverting to the approved Vite 5.x range restores the project-approved dependency policy but leaves `npm audit` reporting Vite/esbuild development-server advisories.
**Decision**: Keep PR #6 on the approved Vite 5.x / `@vitejs/plugin-react` 4.x major ranges and temporarily accept the dev-server audit warning for this PR. Do not reintroduce the Vite major upgrade in PR #6.
**Rationale**: The PR's scope is dashboard/detail UI against dummy JSON. A major build-tool upgrade is broader than the feature and requires explicit approval plus full manual demo-flow retest. The reported advisories affect the dev-server/tooling path rather than the generated static production bundle.
**Trade-offs**: `npm audit` remains non-zero until a separately approved Vite major upgrade lands.
**Consequences**: PR #6 can be reviewed for merge based on build/lint/copy-safety checks, with `npm audit` recorded as an accepted temporary risk. A future dependency-maintenance task should request approval for the Vite major upgrade and perform the required manual demo-flow retest.

---

### ADR-013: `/api/issues` degrades to `200` + static fallback, not `503`, when live data is unavailable

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Backend Implementer (flagged for PM/Frontend confirmation)

**Context**: `TASK-010` wired `/api/issues`, `/api/issues/:id`, and `/api/issues/:id/history` to real Postgres reads via `app/db/session.py::get_db()`. As of this task, `TASK-007`/`TASK-008` had not produced any `market_snapshots`/`market_metrics` rows, and `DATABASE_URL` is also commonly unset in local dev. Technical Design §5 mentions `503` for a "degrade to last-known-good data" case, which is ambiguous about whether the response body is still served on a `503`.
**Decision**: When `DATABASE_URL` is unset, a live query fails, or `market_snapshots` has zero rows, the affected endpoints return `200` with the existing static sample dataset (`_FALLBACK_ISSUES` in `app/api/routes/issues.py`) and its fixed `data_as_of`, not `503`. Every fallback is logged via `logger.warning("FALLBACK: ...")` with the specific reason, so it can never become a silent permanent substitute once real data lands.
**Rationale**: Matches `reports/day-2-work-allocation.md`'s Judging Q&A seed ("the API and frontend keep a static/last-known-good fallback path with honest timestamps") and `TASK-012`'s DoD ("retain a static fallback for demo resilience") - a `503` would force the frontend into an error state instead of a usable demo dashboard.
**Trade-offs**: `503` as specified in Technical Design §5 is not implemented; if a future need arises to distinguish "serving fallback data" from "serving live data" at the HTTP layer (e.g. for monitoring), that will require either a new response field (contract change, needs approval) or an out-of-band signal (e.g. a response header), not implemented here.
**Consequences**: `backend/API_CONTRACT.md`'s Error shape section now documents this instead of the "not yet triggerable" `503` placeholder. Flagged for explicit PM/Frontend confirmation the same way ADR-008 was, since it affects demo behavior even though it does not change the response schema.
