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
- **Status**: Proposed (pending PM/Frontend sign-off)
- **Decided by**: Backend Implementer

**Context**: Technical Design §5 specifies returning HTTP `204` with a JSON body hint `{"status": "not_yet_generated"}` when no AI report exists yet for an issue. HTTP `204 No Content` cannot carry a response body per spec — most clients discard it, so the frontend would never see the hint.
**Decision**: TASK-003's draft contract (`backend/API_CONTRACT.md`) instead returns `200 OK` with `{"status": "not_yet_generated"}`, keeping the same neutral-empty-state intent without the invalid HTTP semantics.
**Rationale**: Preserves the product intent (no error state; frontend shows a neutral placeholder) while fixing a factual protocol error in the source spec.
**Trade-offs**: Diverges from the literal Technical Design wording; needs PM/Frontend confirmation before other implementation depends on it.
**Consequences**: If PM prefers a different resolution (e.g. `404` with a distinguishing error code), update `backend/API_CONTRACT.md`, `backend/app/schemas/issues.py::ReportNotYetGenerated`, and the corresponding route/tests together.

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
