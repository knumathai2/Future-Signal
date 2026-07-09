<!--
Purpose:        Track known bugs, technical debt, and temporary workarounds
Owner:          Debugger / Reviewer
Update Trigger: New bug found, issue resolved, new tech debt identified
Harness Version: 1.1
-->

# Known Issues — Outlook Signals

_Last updated: 2026-07-09_

## Active Bugs

| ID | Severity | Description | Found | Owner |
|----|----------|-------------|-------|-------|
| ISS-004 | Medium | Development Supabase schema is applied, but live data tables are empty, so the API serves the documented static fallback data. | 2026-07-09 | Data/AI + Backend |

## Technical Debt

| ID | Description | Impact | Target Resolution |
|----|-------------|--------|-------------------|
| TD-001 | Frontend production build reports a chunk-size warning, likely from Recharts in the first bundle. | Non-blocking for the MVP; initial load could be optimized later. | Consider lazy-loading the detail/chart route after MVP flow stabilizes. |
| TD-002 | `npm audit` reports Vite/esbuild dev-server vulnerabilities when frontend dependencies stay within the approved Vite 5.x major range. | Dev-server security warning; clearing it requires a Vite major upgrade that needs human approval. | Temporarily accepted for PR #6 by ADR-010; revisit in a dependency-maintenance task with explicit Vite major-upgrade approval and manual demo-flow retest. |
| TD-003 | Backend dependency install fails on this machine's default Python 3.9 because the pinned `psycopg[binary]==3.2.3` binary package is not available for that local runtime/platform combination. | A new contributor using default `python3` may be blocked before running backend tests. | Use Python 3.11 for local setup, as documented in `backend/README.md`; later decide whether to formalize a minimum Python version in backend tooling. |
| TD-007 | `backend/API_CONTRACT.md`'s Error shape section documents invalid `window`/`sort` as FastAPI's current `422` behavior rather than forcing the original `400` plan. | Low; frontend should code against `422`. Changing it to `400` would be a public behavior change beyond the TASK-010 conflict-resolution scope. | Leave documented as actual behavior unless PM/Frontend request a separate API-error normalization task. |
| TD-009 | The live API/static backend fallback path can still return English sample issue titles while the frontend dummy fallback is Korean. | Demo language consistency risk if the backend fallback is used during presentation. | Add a precise Day 5 fallback/demo note if backend fallback data is used in presentation, or localize the backend sample in a separate copy task. |


## Resolved

| ID | Description | Resolved | Method |
|----|-------------|----------|--------|
| ISS-001 | Detail chart could not display a trend for 24h/7d/30d when the API history path returned only one point; this was not caused by the 5pp inflection-marker threshold. | 2026-07-08 | Frontend now renders an explicit insufficient-history state when the visible chart window has fewer than two history points. |
| DQ-001 | API no-report-yet response shape needed PM/Frontend sign-off. | 2026-07-08 | ADR-008 accepted `200 {"status": "not_yet_generated"}` as the canonical response. |
| TD-004 | `backend/API_CONTRACT.md` still contained stale "draft/open item" wording for the report-empty response even though ADR-008 accepted `200 {"status": "not_yet_generated"}`. | 2026-07-08 | Cleaned up during `TASK-010` - "Open item for PM sign-off" section now states the accepted behavior as final; response shape unchanged. |
| TD-005 | PR #9's TASK-007 normalized sample artifact was not shaped for the accepted downstream schema and lacked structured skip/error details. | 2026-07-08 | Fixed by the PR #9 review-fix commit recorded in ADR-014; verified during `TASK-008` that the merged `normalized_samples.json` has all required top-level fields (0 nulls across 50 records) and `skipped_records.json` carries structured reasons. |
| TD-006 | PR #9's committed sample artifact stored raw external descriptions that could trip the project wording lint if used as fallback/display data. | 2026-07-08 | Fixed by ADR-014 (`description_policy: raw_source_descriptions_omitted`); verified during `TASK-008`'s dependency check that no raw source text remains in the committed artifact. |
| TD-008 | `TASK-008`'s `market_metrics.confidence_level` lacked `caution_low_activity` and `caution_high_volatility`. | 2026-07-09 | Fixed in TASK-036 by ADR-019. Implemented conservative thresholds based on sample data. |
| DQ-002 | Inflection-point threshold needed fixed-threshold vs. volatility-adjusted resolution. | 2026-07-09 | Resolved for MVP by ADR-019: use the existing ±5pp `expectation_shift` threshold and defer richer volatility-adjusted logic. |
| DQ-003 | Confidence/caution badge approach needed composite vs. qualitative-state resolution. | 2026-07-09 | Resolved for MVP by ADR-019 and TASK-014: keep qualitative caution states and render supported levels consistently. |
| TD-010 | `GET /api/issues/{id}/report` was not wired to latest successful `ai_reports` rows. | 2026-07-09 | Fixed in `TASK-039`: live mode now returns the latest successful stored report, excludes failed rows, and preserves `not_yet_generated` for absent or failed reads without changing the response shape. |
| ISS-002 | Direct Supabase database route was not reachable locally over IPv6. | 2026-07-09 | Resolved by switching to the Supabase pooler URL and adding the missing `DATABASE_URL=` key in `backend/.env`; read-only `select 1` now succeeds. |
| ISS-003 | Supabase DB was reachable but app schema was not applied. | 2026-07-09 | Resolved by applying `backend/migrations/001_initial_schema.sql` to the configured development Supabase DB after explicit human approval; expected tables and `pgcrypto` are present. |

## Open Design Questions Carried From Planning Docs

Not bugs, but unresolved decisions that can still affect demo readiness - resolve
them before Day 5 lock if they become relevant to the active path:

- Category taxonomy: Polymarket's own tags vs. manual mapping (PRD §20.4, Service Design §12.1)
- Static-JSON fallback path finalization for full demo operations: API/frontend fallback behavior is implemented and documented by ADR-013; Day 4-5 still need backup captures or demo-script handling.
- `heat_score` weighting formula — start simple, tune once real data is visible (Technical Design §16.2)

## Known Data Issues

- `resolutionSource`: Often empty or missing in both the event and market data. (Found during TASK-004 spike)


## Issue Template

```
### ISS-XXX: [Title]
- **Severity**: Critical | High | Medium | Low
- **Found**: YYYY-MM-DD
- **Reproduction steps**:
- **Root cause**:
- **Workaround**:
- **Permanent fix direction**:
```

### ISS-001: Detail chart blank with one-point history
- **Severity**: High
- **Found**: 2026-07-08
- **Resolved**: 2026-07-08
- **Reproduction steps**:
  1. Run the frontend against the backend fallback/live path.
  2. Open an issue detail screen.
  3. Toggle the chart window between 24h, 7d, and 30d.
  4. Observe that the chart area can look blank because the history response contains only one point.
- **Root cause**:
  - `frontend/src/App.tsx` fetches detail history once with `window=30d`.
  - `frontend/src/components/IssueTrendChart.tsx` then slices that same history array to 2, 8, or 31 points for 24h/7d/30d.
  - `backend/app/api/routes/issues.py` returns only the latest snapshot point in the static fallback path and also falls back to a single latest point when live history is empty or query loading fails.
  - Recharts cannot draw a visible line segment from one point, and the chart line has `dot={false}`; with no inflection marker, this reads as an empty chart.
  - The 5pp threshold only controls inflection-point markers/signals, not whether the chart line should be displayed.
- **Workaround**:
  - Use frontend forced error/static fallback data, which contains generated multi-point history, or seed/query enough market snapshots for the selected window.
- **Permanent fix direction**:
  - Completed frontend fix: `IssueTrendChart` renders an explicit
    insufficient-history state when fewer than two visible history points
    exist.
  - Backend/API shape was preserved; multi-point fallback history can still be
    considered later for richer demo data, but it is no longer required to avoid
    a blank/misleading chart state.

### ISS-002: Direct Supabase database route is not reachable locally
- **Severity**: Medium
- **Found**: 2026-07-09
- **Reproduction steps**:
  1. Ensure `backend/.env` contains a `DATABASE_URL`.
  2. From the repo root, load `backend/.env` and attempt a read-only
     `select 1` through SQLAlchemy.
  3. Observe an `OperationalError` after DNS resolution succeeds but the
     direct host connection cannot be routed from this machine.
- **Root cause**:
  - The configured direct Supabase DB URL has the expected shape, including
    host, port, user, password, and database name.
  - `psycopg2-binary==2.9.10` was added on 2026-07-09 so provider-copied
    `postgresql://...` URLs can be used without rewriting the driver scheme.
  - DNS now resolves, but the direct Supabase host resolves to an IPv6 address
    that this local network cannot route (`No route to host`).
  - The exact URL and secret values were not printed.
- **Workaround**:
  - Keep the FastAPI server running; the implemented `/api/issues` fallback path
    serves static sample data with an honest `data_as_of` timestamp.
- **Permanent fix direction**:
  - Replace the direct Supabase connection string with the Supabase pooler
    connection string from the dashboard, then restart the backend.
  - Do not apply migrations or write to any shared database without the
    existing human approval gate.

### ISS-003: Supabase DB is reachable but app schema is not applied
- **Severity**: Medium
- **Found**: 2026-07-09
- **Resolved**: 2026-07-09
- **Reproduction steps**:
  1. Configure `backend/.env` with the Supabase pooler `DATABASE_URL`.
  2. Confirm a read-only SQLAlchemy `select 1` succeeds.
  3. Start the backend and request `/api/issues?limit=2`.
  4. Observe the API returns static fallback data while the backend logs
     `relation "market_snapshots" does not exist`.
- **Root cause**:
  - The database connection is now valid, but the draft application schema has
    not been applied to this Supabase database.
- **Workaround**:
  - Keep using the documented static fallback data for local UI inspection.
- **Permanent fix direction**:
  - Completed: applied `backend/migrations/001_initial_schema.sql` to the
    configured development Supabase DB after explicit human approval.
  - Seed or collect data before expecting live issue rows.

### ISS-004: Supabase app tables are present but empty
- **Severity**: Medium
- **Found**: 2026-07-09
- **Reproduction steps**:
  1. Configure `backend/.env` with the Supabase pooler `DATABASE_URL`.
  2. Confirm a read-only SQLAlchemy `select 1` succeeds.
  3. Confirm `backend/migrations/001_initial_schema.sql` has been applied.
  4. Request `/api/issues?limit=2`.
  5. Observe static fallback data while the backend logs no live snapshot data.
- **Root cause**:
  - The app tables exist but have zero rows. In particular, `market_snapshots`
    is empty, so the live read path correctly falls back instead of fabricating
    issue data.
- **Workaround**:
  - Keep using the documented static fallback data for local UI inspection.
- **Permanent fix direction**:
  - Run the approved data seed/collector path against the development DB only
    after confirming the intended data-writing scope.
