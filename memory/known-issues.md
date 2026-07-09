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
| — | — | No active bugs currently recorded. | — | — |

## Technical Debt

| ID | Description | Impact | Target Resolution |
|----|-------------|--------|-------------------|
| TD-001 | Frontend production build reports a chunk-size warning, likely from Recharts in the first bundle. | Non-blocking for the MVP; initial load could be optimized later. | Consider lazy-loading the detail/chart route after MVP flow stabilizes. |
| TD-002 | `npm audit` reports Vite/esbuild dev-server vulnerabilities when frontend dependencies stay within the approved Vite 5.x major range. | Dev-server security warning; clearing it requires a Vite major upgrade that needs human approval. | Temporarily accepted for PR #6 by ADR-010; revisit in a dependency-maintenance task with explicit Vite major-upgrade approval and manual demo-flow retest. |
| TD-003 | Backend dependency install fails on this machine's default Python 3.9 because the pinned `psycopg[binary]==3.2.3` binary package is not available for that local runtime/platform combination. | A new contributor using default `python3` may be blocked before running backend tests. | Use Python 3.11 for local setup, as documented in `backend/README.md`; later decide whether to formalize a minimum Python version in backend tooling. |
| TD-007 | `backend/API_CONTRACT.md`'s Error shape section documents invalid `window`/`sort` as FastAPI's current `422` behavior rather than forcing the original `400` plan. | Low; frontend should code against `422`. Changing it to `400` would be a public behavior change beyond the TASK-010 conflict-resolution scope. | Leave documented as actual behavior unless PM/Frontend request a separate API-error normalization task. |


## Resolved

| ID | Description | Resolved | Method |
|----|-------------|----------|--------|
| ISS-001 | Detail chart could not display a trend for 24h/7d/30d when the API history path returned only one point; this was not caused by the 5pp inflection-marker threshold. | 2026-07-08 | Frontend now renders an explicit insufficient-history state when the visible chart window has fewer than two history points. |
| DQ-001 | API no-report-yet response shape needed PM/Frontend sign-off. | 2026-07-08 | ADR-008 accepted `200 {"status": "not_yet_generated"}` as the canonical response. |
| TD-004 | `backend/API_CONTRACT.md` still contained stale "draft/open item" wording for the report-empty response even though ADR-008 accepted `200 {"status": "not_yet_generated"}`. | 2026-07-08 | Cleaned up during `TASK-010` - "Open item for PM sign-off" section now states the accepted behavior as final; response shape unchanged. |
| TD-005 | PR #9's TASK-007 normalized sample artifact was not shaped for the accepted downstream schema and lacked structured skip/error details. | 2026-07-08 | Fixed by the PR #9 review-fix commit recorded in ADR-014; verified during `TASK-008` that the merged `normalized_samples.json` has all required top-level fields (0 nulls across 50 records) and `skipped_records.json` carries structured reasons. |
| TD-006 | PR #9's committed sample artifact stored raw external descriptions that could trip the project wording lint if used as fallback/display data. | 2026-07-08 | Fixed by ADR-014 (`description_policy: raw_source_descriptions_omitted`); verified during `TASK-008`'s dependency check that no raw source text remains in the committed artifact. |
| TD-008 | `TASK-008`'s `market_metrics.confidence_level` lacked `caution_low_activity` and `caution_high_volatility`. | 2026-07-09 | Fixed in TASK-036 by ADR-019. Implemented conservative thresholds based on sample data. |

## Open Design Questions Carried From Planning Docs

Not bugs, but unresolved decisions that will surface as real blockers during the build — resolve these on Day 1-2, don't let them idle:

- Category taxonomy: Polymarket's own tags vs. manual mapping (PRD §20.4, Service Design §12.1)

- Inflection-point threshold: fixed ±5pp vs. volatility-adjusted (PRD §20.6)
- Confidence/caution badge: single composite score vs. separate qualitative badges (Service Design §12.4, UX Design §14.2)
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
