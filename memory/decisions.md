<!--
Purpose:        Key technical decision history in ADR format
Owner:          PM / Backend Implementer
Update Trigger: Record immediately after any significant technical or scope decision
Harness Version: 1.1
-->

# Decision Log — Outlook Signals

_Last updated: 2026-07-09_

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
- **Decided by**: Backend Implementer; confirmed by User / PM gate on 2026-07-08

**Context**: `TASK-010` wired `/api/issues`, `/api/issues/:id`, and `/api/issues/:id/history` to real Postgres reads via `app/db/session.py::get_db()`. As of this task, `TASK-007`/`TASK-008` had not produced any `market_snapshots`/`market_metrics` rows, and `DATABASE_URL` is also commonly unset in local dev. Technical Design §5 mentions `503` for a "degrade to last-known-good data" case, which is ambiguous about whether the response body is still served on a `503`.
**Decision**: When `DATABASE_URL` is unset, a live query fails, or `market_snapshots` has zero rows, the affected endpoints return `200` with the existing static sample dataset (`_FALLBACK_ISSUES` in `app/api/routes/issues.py`) and its fixed `data_as_of`, not `503`. Every fallback is logged via `logger.warning("FALLBACK: ...")` with the specific reason, so it can never become a silent permanent substitute once real data lands.
**Rationale**: Matches `reports/day-2-work-allocation.md`'s Judging Q&A seed ("the API and frontend keep a static/last-known-good fallback path with honest timestamps") and `TASK-012`'s DoD ("retain a static fallback for demo resilience") - a `503` would force the frontend into an error state instead of a usable demo dashboard.
**Trade-offs**: `503` as specified in Technical Design §5 is not implemented; if a future need arises to distinguish "serving fallback data" from "serving live data" at the HTTP layer (e.g. for monitoring), that will require either a new response field (contract change, needs approval) or an out-of-band signal (e.g. a response header), not implemented here.
**Consequences**: `backend/API_CONTRACT.md`'s Error shape section now documents this instead of the "not yet triggerable" `503` placeholder. The PR #10 `CHANGES_REQUESTED` blocker for explicit confirmation is resolved by the 2026-07-08 user/PM-gate follow-up; no response schema change is needed.

---

### ADR-014: TASK-007 normalized artifacts omit raw source descriptions

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Data/AI Implementer, following PR #9 review feedback

**Context**: PR #9 review found that `normalized_samples.json` exposed raw external descriptions under the top-level `description` field, and some records had null required downstream fields such as `volume_24h` or `end_date`.
**Decision**: The batch collector now emits a display-safe `description: str` generated by the collector, omits raw source descriptions from the sample artifact, and records `source_metadata.description_policy = raw_source_descriptions_omitted`. Candidate records missing required downstream fields are skipped with structured reasons in `skipped_records.json`.
**Rationale**: TASK-008/TASK-010 need a stable handoff contract, while fallback/display consumers must not accidentally render raw external source text.
**Trade-offs**: The sample description is intentionally generic until a later, policy-reviewed description-generation path exists.
**Consequences**: The refreshed 50-record `normalized_samples.json` has no null required fields, all top-level descriptions are strings, and invalid candidates are quarantined rather than producing partial normalized records.

---

### ADR-015: TASK-008 bootstraps `markets`/`market_outcomes` rows and ships a P0-only metric set

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Data/AI Implementer

**Context**: Technical Design §6 steps 3-5 (`app/core/snapshot_metrics.py`) need a stable `markets.id` UUID to write `market_snapshots`/`market_metrics` rows against, but TASK-007's normalize step (steps 1-2) never touches the database - it only produces normalized dicts/JSON, confirmed by `collector.py` having zero SQLAlchemy imports. No other task in `tasks/active.md` claims ownership of populating `markets`/`market_outcomes` from normalized data. Separately, Service Design §5's metric table marks `change_24h`, `change_7d`, the simplified "market confidence score," and the simplified "issue heat score" as P0, while `volatility_score`, `attention_score`, and a `caution_low_activity`/`caution_high_volatility` confidence split are P1 or an open design question (`known-issues.md`'s "Minimum volume/liquidity floor" item).
**Decision**: (1) `snapshot_metrics.py` does a minimal get-or-create of `markets` (by `polymarket_condition_id`) and its one tracked `market_outcomes` row as plumbing inside steps 3-4, updating only `markets.last_seen_at`/`status` in place (the one exception to append-only per §4.10) - no new table or column. (2) `market_metrics.confidence_level` is populated with only `sufficient`/`insufficient_data` this task; `caution_low_activity`/`caution_high_volatility` are left unused pending the open volume/liquidity-floor decision. (3) `heat_score` uses a placeholder bounded formula (`|change_24h| * 500 + min(volume_24h / 50, 30)`, capped at 100); `volatility_score`/`attention_score` are always `null` (P1, not computed).
**Rationale**: Building markets/outcomes rows here is the only place in the current step 1-8 pipeline where it can happen without inventing a new task; it satisfies the existing schema's FK contract rather than adding a feature. Withholding `caution_low_activity` avoids fabricating an un-approved policy threshold under the project's no-fabrication rule, applied to thresholds as well as data. The heat_score formula is explicitly sanctioned as a starting point by Service Design §5 ("can start as a simple weighted rank... don't need full composite v1") and by `known-issues.md`'s existing "heat_score weighting formula - start simple, tune once real data is visible" note.
**Trade-offs**: `confidence_level` currently only distinguishes "have a 24h change" from "don't" - it does not yet flag a technically-sufficient-history market that's actually low-volume/thin or high-volatility. `heat_score` values are not yet tuned against real batch behavior.
**Consequences**: TASK-009's `±5pp` threshold detector can rely on `change_24h` as implemented. A future task should resolve the volume/liquidity floor open question and add `volatility_score` before `caution_low_activity`/`caution_high_volatility` can be populated - tracked in `known-issues.md`.

---

### ADR-016: TASK-009 signal detection reads `market_metrics` by `computed_at`, decoupled from TASK-008's run function

- **Date**: 2026-07-08
- **Status**: Accepted (implementation-scope note, not a policy/threshold/schema change - no human approval gate applies)
- **Decided by**: Data/AI Implementer

**Context**: Technical Design §8 step 6 (signal detection) runs immediately after step 5 (metrics) computes each market's `change_24h` in the same batch pass. TASK-008's `run_snapshot_and_metrics()` (`app/core/snapshot_metrics.py`) already computes and inserts `market_metrics` rows for a run, but its return type (`BatchRunResult`/`MarketRunOutcome`) does not carry the inserted `MarketMetric.id` or the row objects themselves - only a summary (`change_24h`, `confidence_level`, etc.) per market.
**Decision**: `app/core/signal_detection.py` does not modify TASK-008's return type or call signature. Instead, `detect_signals_for_run(db, run_timestamp)` re-queries `market_metrics` for rows where `computed_at == run_timestamp` (the same timestamp `run_snapshot_and_metrics` already stamps every row in a run with), then evaluates each against the ±5pp threshold.
**Rationale**: Keeps TASK-008's already-reviewed/merged module untouched (lower regression risk) while still giving step 6 exactly the metrics computed in "this run." The two modules compose via `detect_signals_for_run(db, run_snapshot_and_metrics(...).run_timestamp)` without any shared-object coupling.
**Trade-offs**: One extra `SELECT` per run instead of reusing in-memory objects from step 5; at hackathon scale (30-50 markets, a handful of runs/day) this is not a performance concern. `issue_signals.detail` therefore stores `metric_id`/`change_24h`/`threshold` rather than the bounding `market_snapshots` ids mentioned as an example in Technical Design §4.5, since TASK-008 doesn't expose the reference snapshot id used inside `compute_change_for_window` - the schema's `detail` field is explicitly "free-form extra context," not a fixed contract, so this is populated with what's actually available rather than fabricated.
**Consequences**: A market's `expectation_shift` signal can be traced back to its exact `market_metrics` row via `detail.metric_id`. If a future task needs snapshot-id-level detail, `compute_change_for_window` in `snapshot_metrics.py` would need to additionally return the reference snapshot's id - not done here to avoid touching TASK-008's merged module for a need this task doesn't have.

---

### ADR-017: Day 3 active work limited to detail, chart, and caution-badge readiness

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 2 closed with a usable data/API/dashboard baseline. PRD §14 defines Day 3 as the detail screen, chart, tooltip, inflection-point markers, and interpretation-caution badge day, while template summary generation belongs to the Day 4 demo-flow milestone.
**Decision**: Open Day 3 active work for `TASK-013`, `TASK-014`, `TASK-017`, `TASK-035`, and `TASK-036`. Treat `TASK-015` as deferred until the detail/chart/badge path is stable, unless PM explicitly reassigns it late in Day 3.
**Rationale**: The highest current demo risk is a detail view that shows a chart or caution badge in a confusing way. Stabilizing that path first protects the core Home -> Detail -> Chart flow before adding the template summary generator.
**Trade-offs**: Data/AI report work may start later than the original `TASK-015` Day 3-4 range suggests. This keeps the team from splitting attention before the core detail path is trustworthy.
**Consequences**: `tasks/active.md` is the Day 3 source of execution truth; `reports/day-3-work-allocation.md` records the sequence and guardrails. Shared/dev database schema application, public API response-shape changes, new dependencies, deployment work, and wording-policy changes remain approval-gated by `AGENTS.md`.

---

### ADR-018: Detail chart windows require baseline-covered history

- **Date**: 2026-07-09
- **Status**: Accepted (TASK-013 implementation decision)
- **Decided by**: Frontend Implementer

**Context**: The Day 3 detail chart must support 24h, 7d, and 30d selection with honest insufficient-history states. The existing frontend sliced the last 2/8/31 points and displayed `change30d ?? change7d`, which could make a short history look like a valid longer-window chart.
**Decision**: For each selected chart window, the frontend now requires at least one history point at or before that window's baseline plus a later point before rendering a line chart. If that baseline is unavailable, the chart shows an insufficient-history state. The 30d metric displays only an actual 30d history-derived change, not a 7d fallback.
**Rationale**: This matches the no-fabrication rule used by backend metrics and avoids overstating sparse API/fallback history during the demo.
**Trade-offs**: A window may show an insufficient-history state even when it has several recent points, if those points do not reach the requested baseline. This is preferable to stretching a shorter span into a longer-window interpretation.
**Consequences**: `frontend/src/utils/history.ts` is the shared frontend helper for window coverage. The detail chart still preserves the accepted API response shape and uses API-provided `signals` when present, with local adjacent 5pp detection only as a fallback marker source.

---

### ADR-019: Caution-badge thresholds and expectation-shift marker handoff (TASK-036)

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: Data/AI Implementer

**Context**: MVP interpretation caution logic needs to handle `caution_low_activity` and `caution_high_volatility` without waiting for a complex volume/liquidity floor calculation, and `expectation_shift` markers need a clear consumption contract.
**Decision**:
1. **Caution Thresholds**: Implemented conservative hardcoded thresholds in `compute_confidence_level` based on sample data: 500 USDC for `volume_24h`, 1000 USDC for `liquidity`, and >15pp absolute change for `change_24h`.
2. **Precedence**: `insufficient_data` continues to take precedence over any activity or volatility caution state if history is lacking.
3. **Marker Consumption Contract**: The backend `/api/issues/:id` endpoint will query `issue_signals` for any `expectation_shift` (±5pp threshold, medium severity) rows related to the market. The frontend will consume these rows to render "Expectation Shift" visual markers on the detail chart at the `triggered_at` timestamps, enabling users to visually align shifts with their own context without implying causation.
**Rationale**: Uses the existing schema and Enum values for `confidence_level` without adding new schema fields, keeping the MVP lightweight. Documenting the marker contract ensures frontend/backend alignment without extending P1 metrics.
**Trade-offs**: Hardcoded thresholds may need adjustment as real-world Polymarket volume changes, and using absolute 24h change as a volatility proxy is less precise than a full `volatility_score`.
**Consequences**: Closes MVP path for TD-008. Backend and frontend implementers can proceed with API/UI integration for caution badges and expectation-shift markers.

---

### ADR-020: Day 4 active work limited to summary and demo-flow completion

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 3 closed the detail/chart/caution path, and latest
`origin/main` at `af83f7e` includes the Day 3 closeout merge. PRD section 14
defines Day 4 as template summaries, demo-flow completion, fallback readiness,
manual event candidates, and a deck/script draft.
**Decision**: Open Day 4 active work for `TASK-015`, `TASK-039`, `TASK-016`,
`TASK-019`, `TASK-040`, and `TASK-018`. Keep P1 category/feed/extra-metric
work deferred until the Day 4 P0 path is complete. Treat any paid external AI
provider call, schema change, deployment, infrastructure change, public API
shape change, or shared/production database write as approval-gated.
**Rationale**: The remaining demo risk is not feature breadth; it is whether
the Home -> Detail -> Chart -> Summary path is coherent, safe, and rehearsable.
This sequence lets Data/AI and Backend unblock Frontend report display while PM
prepares the demo story and final wording pass.
**Trade-offs**: General UI polish and P1 metrics remain deferred even though
they could improve perceived quality. The allocation prefers a complete and
guarded summary/demo path over broader scope.
**Consequences**: `tasks/active.md` is the Day 4 execution source of truth, and
`reports/day-4-work-allocation.md` records the sequencing and guardrails.
`TASK-025` remains stretch-only unless the Day 4 checklist is already satisfied.

---

### ADR-021: Report API reads latest successful stored reports while history empty states stay honest

- **Date**: 2026-07-09
- **Status**: Accepted (TASK-039 implementation decision)
- **Decided by**: Backend Implementer

**Context**: PR #29 originally changed `/api/issues/{id}/history` to return an empty `points` array when history was missing or the query failed, but it predated the Day 4 `TASK-039` ledger on `main`. Day 4 `TASK-039` requires `/api/issues/{id}/report` to read latest successful `ai_reports` rows while preserving the accepted `not_yet_generated` empty state.
**Decision**: Preserve the history no-fabrication behavior: live and static fallback history responses return `points: []` when no history is available or the history query fails. Also wire the live report endpoint to the latest successful `ai_reports` row for the issue. Failed report rows are never served; absent reports or report-read failures return the accepted `{"status": "not_yet_generated"}` shape. Static fallback mode keeps its demo-safe sample report.
**Rationale**: Empty history is more honest than plotting a fabricated latest point, and serving only successful stored reports keeps the API read-only and decoupled from report generation. The response shapes stay unchanged, so frontend integration can keep the existing success/empty-state contract.
**Trade-offs**: Static fallback history may show no chart line until richer fallback history is deliberately added. Static fallback report content remains a curated sample, so `TD-009` still needs a Day 5 language/demo fallback note if backend fallback data is used in presentation.
**Consequences**: `TASK-039` is complete for the backend read path. Backend tests now cover latest successful report selection, failed-report exclusion, report-query failure fallback, report unknown-id behavior, and empty history fallback behavior without any schema, dependency, infrastructure, deployment, or public API shape change.

---

### ADR-022: AI provider selection - OpenAI, live call approved for TASK-015 ⚠️ HUMAN APPROVAL

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User (human), implementing Data/AI Implementer

**Context**: Technical Design §9 leaves the LLM provider as "Claude or OpenAI."
`reports/day-4-work-allocation.md` (ADR-020) had defaulted `TASK-015`'s
execution to deterministic template generation with any real provider hook
"disabled or stubbed until approved," since calling a paid external AI API is
an `AGENTS.md` Absolute Restriction requiring explicit human approval, and AI
Provider Selection is itself a Human Approval Gate. Before implementation,
the user was asked (1) which provider to select and (2) whether to follow
the Day-4 deterministic default or wire a real live call now. The user chose
OpenAI, then explicitly chose to override the Day-4 default and wire the real
call rather than stub it.
**Decision**: OpenAI is the selected AI provider. `app/core/ai_report.py`
implements `OpenAIReportClient` (real OpenAI Chat Completions call, JSON-mode
response, `response_format={"type": "json_object"}`) behind the `LLMClient`
protocol, constructed explicitly via `build_openai_client()` - never
constructed or called implicitly at import time. `openai==2.44.0` was added
to `backend/requirements.txt` (new dependency, covered by the same user
approval). Settings gained `OPENAI_API_KEY`/`OPENAI_MODEL`
(`app/core/config.py`, `.env.example`) - no key is committed, and no key is
present in this development environment, so no real network call to OpenAI
has actually been made or billed in this session; all tests exercise the
pipeline against a fake `LLMClient`.
**Rationale**: Explicit, repeated human approval was obtained in-session for
both the provider choice and the decision to wire a live call rather than the
deterministic-template default, satisfying both the paid-API and
AI-Provider-Selection approval gates in `AGENTS.md`.
**Trade-offs**: This departs from `reports/day-4-work-allocation.md`'s stated
Day 4 default (deterministic template, no live provider) - that allocation
doc is not being edited to match, since it is PM's dated allocation record;
this ADR is the override of record. Real API cost is now possible the first
time someone runs the batch job with `OPENAI_API_KEY` set, unlike the
deterministic-default path.
**Consequences**: Before any live/demo run of `app/core/ai_report_batch.py`
with a real key, confirm the key is scoped/budgeted appropriately - this ADR
approves the architecture and provider, not an unbounded number of live calls.
2026-07-09 follow-up: the user clarified that the provided `OPENAI_API_KEY`
may be used without asking for separate per-run approval for project-scoped
OpenAI report generation. This standing OpenAI-call approval does not approve
shared/dev database writes, deployments, schema changes, dependency changes, or
public API shape changes; those gates remain separate. `memory/architecture.md`
and `tasks/completed.md` should reference this ADR for TASK-015's provider
choice.

---

### ADR-023: Add psycopg2-binary for provider-copied Postgres URLs

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User (human), implementing Debugger

**Context**: The backend already depended on `psycopg[binary]` and documented
`postgresql+psycopg://...` as the preferred SQLAlchemy URL form. Supabase
dashboard connection strings are commonly copied as plain `postgresql://...`.
With that form, SQLAlchemy defaults to the `psycopg2` driver. Local DB
connectivity checks therefore failed with `ModuleNotFoundError: No module named
'psycopg2'` even after the Supabase host and URL parsing were corrected.
**Decision**: Add `psycopg2-binary==2.9.10` to the backend runtime
dependencies while keeping `psycopg[binary]==3.2.3` in place.
**Rationale**: This lets the backend accept provider-copied Supabase
`postgresql://...` URLs without requiring every developer to rewrite the URL
scheme to `postgresql+psycopg://...`. It also keeps the existing psycopg3 path
available for environments that prefer explicit driver selection.
**Trade-offs**: The backend now carries two Postgres drivers. That is a small
dependency increase, but it reduces setup friction during the hackathon.
**Consequences**: `backend/requirements.txt`, `dependencies.md`,
`backend/README.md`, `commands.md`, and `backend/migrations/README.md` document
the supported URL forms and the Supabase direct-host IPv6 fallback path. Live DB
connectivity may still fail on local networks that cannot route Supabase's
direct IPv6 host; use the Supabase pooler connection string in that case.

---

### ADR-024: Apply initial schema to development Supabase DB

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User (human), implementing Debugger

**Context**: After switching `DATABASE_URL` to the Supabase pooler URL,
read-only connectivity succeeded, but live API reads fell back because the
database did not contain application tables such as `market_snapshots`.
`backend/migrations/001_initial_schema.sql` had previously been accepted as
the schema draft but remained unapplied under ADR-011.
**Decision**: With explicit user approval, apply
`backend/migrations/001_initial_schema.sql` to the currently configured
development Supabase database.
**Rationale**: The backend live read path requires the accepted app tables
before it can distinguish "no live rows yet" from "schema missing." Applying
the initial schema unblocks the data seed/collector path while keeping public
API shapes unchanged.
**Trade-offs**: This creates tables in the configured Supabase database. The
tables are currently empty, so user-facing issue routes still serve the
documented static fallback until snapshot/metric data is inserted.
**Consequences**: Expected tables and the `pgcrypto` extension are present in
the development DB. Applying this migration or future schema changes to any
other shared or production database remains approval-gated. The next live-data
step is an approved seed/collector write path, not another schema change.

---

### ADR-025: Local/dev historical seed path for DB-backed charts

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User request, implementing Debugger

**Context**: `ISS-004` was resolved by inserting one live snapshot and metric
row per normalized issue into the configured development DB, which made
`/api/issues` DB-backed. The detail chart still needed older snapshot points:
with only one point per issue, the frontend correctly shows an
insufficient-history state rather than fabricating a trend.
**Decision**: Add `backend/app/core/historical_seed.py` as the approved
local/dev path for demo chart history. It fetches CLOB price-history points for
normalized `price_history_token`s, appends missing timestamps to
`market_snapshots`, inserts a fresh latest `market_metrics` row, runs the
existing expectation-shift detector for those metric rows, and records a
`data_collection_logs` audit row. The CLI refuses to write unless `ENV` is
`local`, `dev`, `development`, or `test`, and
`--confirm-local-dev-write` is present.
**Rationale**: This keeps the chart path live and DB-backed without changing
schema, public API shapes, frontend behavior, or safety policy. It also
preserves the append-only model: existing snapshots/metrics remain untouched,
and repeated runs skip already-present history timestamps.
**Limitations**: Historical CLOB price history supplies chart values, but not
historical volume/liquidity at each point. The seed stores volume/liquidity only
when an inserted point is also the newest known snapshot, and otherwise keeps
those auxiliary fields null; the latest metric still uses the latest available
snapshot plus normalized current activity/liquidity values where needed for the
existing caution calculation.
**Consequences**: Demo prep can now choose between waiting for additional
collector cycles or running the guarded historical seed command documented in
`backend/README.md`. Writing to any shared/prod database remains outside this
approval and must be confirmed separately under `AGENTS.md`.

---

### ADR-026: Combined 24h data and AI report batch

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User request, implementing Data/AI Implementer

**Context**: The implementation had separate modules for snapshot/metric
generation, expectation-shift signal detection, and AI report generation.
As a result, collecting data did not automatically create stored AI summaries,
and there was no checked-in 24h schedule. The user requested four concrete
goals: generate AI summaries for the current DB state, connect data/metric/
signal generation to AI summary generation, run every 24h, and provide a
development-only manual generation path without adding UI.
**Decision**: Add `backend/app/core/scheduled_batch.py` as the combined write
path: normalized/live fetched data -> snapshots/metrics -> signals -> AI
reports -> `data_collection_logs`. Add `--reports-only` for development/demo
AI summary generation against the latest existing metric run. Add
`.github/workflows/daily-batch.yml` to run the combined batch every 24h via
GitHub Actions, with manual `workflow_dispatch` support. Use existing schema,
dependencies, and public API shapes.
**Rationale**: This matches the Technical Design step-8 intent while keeping
the user-facing API read-only and avoiding a UI-only trigger that could be
misread as an end-user action.
**Trade-offs**: The scheduled workflow depends on valid `DATABASE_URL` and
`OPENAI_API_KEY` secrets. If report generation fails, the CLI now exits
non-zero so the workflow surfaces the failure instead of silently producing no
stored summaries.
**Consequences**: The current configured OpenAI key returned `401 Unauthorized`
during the first reports-only run. That run inserted failed `ai_reports` audit
rows but no successful summaries; the report endpoint still returns the
accepted `not_yet_generated` state until the key is corrected and the
reports-only command is rerun.
