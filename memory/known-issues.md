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

## Technical Debt

| ID | Description | Impact | Target Resolution |
|----|-------------|--------|-------------------|
| TD-001 | Frontend production build reports a chunk-size warning, likely from Recharts in the first bundle. | Non-blocking for the MVP; initial load could be optimized later. | Consider lazy-loading the detail/chart route after MVP flow stabilizes. |
| TD-002 | `npm audit` reports Vite/esbuild dev-server vulnerabilities when frontend dependencies stay within the approved Vite 5.x major range. | Dev-server security warning; clearing it requires a Vite major upgrade that needs human approval. | Temporarily accepted for PR #6 by ADR-010; revisit in a dependency-maintenance task with explicit Vite major-upgrade approval and manual demo-flow retest. |
| TD-003 | Backend dependency install fails on this machine's default Python 3.9 because the pinned `psycopg[binary]==3.2.3` binary package is not available for that local runtime/platform combination. | A new contributor using default `python3` may be blocked before running backend tests. | Use Python 3.11 for local setup, as documented in `backend/README.md`; later decide whether to formalize a minimum Python version in backend tooling. |
| TD-007 | `backend/API_CONTRACT.md`'s Error shape section documents invalid `window`/`sort` as FastAPI's current `422` behavior rather than forcing the original `400` plan. | Low; frontend should code against `422`. Changing it to `400` would be a public behavior change beyond the TASK-010 conflict-resolution scope. | Leave documented as actual behavior unless PM/Frontend request a separate API-error normalization task. |
| TD-009 | The live API/static backend fallback path can still return English sample issue titles while the frontend dummy fallback is Korean. | Demo language consistency risk if the backend fallback is used during presentation. | Add a precise Day 5 fallback/demo note if backend fallback data is used in presentation, or localize the backend sample in a separate copy task. |
| TD-011 | Existing successful `ai_reports` rows in the configured development DB may still use the v1 5-section content shape after `TASK-043`. | Non-default or lower-ranked issue detail pages can still show `not_yet_generated` until v2 reports are generated for those issues. The default top-20 heat-sorted issues are now verified with v2 content. | Continue guarded scheduled/manual report generation as needed; AI-provider key use remains covered by ADR-022/ADR-027. |


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
| ISS-004 | Development Supabase schema was applied, but live data tables were empty, so the API served the documented static fallback data. | 2026-07-09 | Resolved for the configured development DB by running the existing collector into a temporary artifact directory, filtering the normalized rows against the project hard-block wording list, and running the approved snapshot/metrics path. Inserted 50 `markets`, 50 `market_outcomes`, 50 `market_snapshots`, and 50 `market_metrics`; verified `/api/issues` and the Vite proxy now return DB-backed payloads. |
| ISS-005 | AI report batch could not use latest historical-seed metric rows because metric timestamps were one microsecond after their source snapshots. | 2026-07-09 | Fixed in `TASK-041`: prompt input lookup now selects the latest snapshot with `captured_at <= market_metrics.computed_at`, tests cover the historical-seed offset and fake-LLM success-row insertion, and approved-only run notes document how to create stored summaries later. |
| ISS-006 | Current configured AI key was rejected by OpenAI's default endpoint because it is OpenRouter-style. | 2026-07-09 | Resolved by ADR-027 and rerun: the batch now selects OpenRouter automatically for `OPENROUTER_API_KEY` or `OPENAI_API_KEY` values with the `sk-or-` prefix. Final checked DB state has `ai_reports_success=29`, latest scheduled log is `scheduled_batch_success`, and the top 10 checked heat-sorted issues return report `success`. |
| ISS-007 | v2 issue-explainer reports were generated but could be hidden behind same-timestamp v1 rows, and category filters used sample values that did not match live DB categories. | 2026-07-09 | Fixed on `debug/ISS-007-v2-report-category-filter`: report reads now require current `PROMPT_VERSION`, report regeneration prefers current-version rows when timestamps tie, `/api/categories` returns broad Korean categories derived from live servable issues, `/api/issues` filtering accepts those labels plus raw stored categories, and the configured DB now has v2 summaries for the default top-20 heat-sorted issues. |

## Open Design Questions Carried From Planning Docs

Not bugs, but unresolved decisions that can still affect demo readiness - resolve
them before Day 5 lock if they become relevant to the active path:

- Category taxonomy follow-up: broad Korean filters are implemented for the demo; a later editorial taxonomy may still refine new source tags as data coverage grows (PRD §20.4, Service Design §12.1)
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
- **Resolved**: 2026-07-09
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
  - Completed for the configured development DB: collector produced 50
    normalized samples in a temporary directory, all 50 passed the hard-block
    wording scan for user-facing fields, and `run_snapshot_and_metrics`
    inserted live rows into `markets`, `market_outcomes`, `market_snapshots`,
    and `market_metrics`.
  - Verified backend `/api/issues` and Vite proxy `/api/issues` return the new
    DB-backed `data_as_of` timestamp instead of the static fallback ID.
  - Follow-up completed: `backend/app/core/historical_seed.py` was run against
    the configured development DB with `1w` and `1m` CLOB history intervals.
    The 50 seeded issues now have live DB-backed 24h/7d metric coverage and
    multi-point chart history.
  - Remaining limitation: 30d full-baseline readiness is still unavailable
    (`0` markets in the latest verification), so the demo should use the `7d`
    chart window unless later source history proves otherwise.

### ISS-005: AI report batch cannot use latest historical-seed metric run
- **Severity**: High
- **Found**: 2026-07-09
- **Status**: Resolved — fixed in `TASK-041`; creating stored dev/demo report
  rows still requires a separately approved database-write generation run
- **Reproduction steps**:
  1. Use the configured development DB after the approved historical seed runs.
  2. Confirm `ai_reports=0` through a read-only DB count or observe
     `/api/issues/{id}/report` returning `{"status":"not_yet_generated"}`.
  3. Inspect the latest `market_metrics.computed_at` values from
     `historical_seed`.
  4. Attempt to build report prompt inputs for the latest run.
- **Root cause**:
  - `historical_seed.metric_timestamp_for_seed()` intentionally writes seeded
    metric timestamps as `latest_snapshot_at + 1 microsecond` so seeded metrics
    are newer than first-run metrics.
  - `build_prompt_inputs_for_market()` previously required an exact
    `MarketSnapshot.captured_at == MarketMetric.computed_at` match.
  - As a result, the latest seeded metrics could qualify for report generation
    but fail prompt-input construction because their source snapshots were one
    microsecond earlier.
- **Impact**:
  - Code readiness is fixed. The configured development DB may still have
    `ai_reports=0` until an explicitly approved database-write generation run
    writes stored summaries.
- **Fix completed**:
  - `build_prompt_inputs_for_market()` now uses the latest snapshot at or
    before `market_metrics.computed_at`, without fabricating values.
  - Tests cover the `+1 microsecond` historical-seed timestamp case,
    future-only snapshot rejection, and `run_ai_report_batch` success-row
    insertion with a fake `LLMClient`.
  - `reports/task-041-report-generation-readiness.md` documents the normal
    no-report empty state before approval and the approved-only saved-summary
    procedure.
  - OpenAI report calls are covered by ADR-022 and the provided-key
    clarification; any shared/dev DB write remains separately approval-gated.

### ISS-006: OpenRouter-style key was sent to OpenAI's default endpoint
- **Severity**: High
- **Found**: 2026-07-09
- **Status**: Resolved
- **Evidence**:
  - The configured environment has both `DATABASE_URL` and `OPENAI_API_KEY`.
  - Running `ENV=local ./.venv/bin/python -m app.core.scheduled_batch
    --reports-only --confirm-local-dev-write` reached OpenAI but received
    `401 Unauthorized` for every attempt.
  - Rerunning the same command for current-DB generation produced the same
    result.
  - Read-only DB counts after the rerun: `ai_reports_total=20`,
    `ai_reports_success=0`, `ai_reports_failed=20`.
  - A same-client minimal OpenAI probe confirms `OPENAI_API_KEY` is present,
    but the configured key is rejected with `AuthenticationError`.
  - A direct OpenAI SDK probe returns `status_code=401` and
    `code=invalid_api_key`; the masked key shape in the provider response
    appears to be OpenRouter-style, so this is an authentication mismatch
    before model access or quota is checked.
- **Impact**:
  - Data/detail/history graph paths work, but the report endpoint returns
    `{"status":"not_yet_generated"}` because failed rows are never served.
- **Fix completed**:
  - Added OpenRouter support without a new dependency: the existing OpenAI SDK
    path now uses `https://openrouter.ai/api/v1` when `OPENROUTER_API_KEY` is
    present or `OPENAI_API_KEY` has the `sk-or-` prefix.
  - For OpenRouter, unqualified model names such as `gpt-4o-mini` are sent as
    `openai/gpt-4o-mini`.
  - Reran the reports-only command after fixing the current-DB selector to use
    each market's latest metric row. Final checked state:
    `ai_reports_total=49`, `ai_reports_success=29`,
    `ai_reports_failed=20`, latest log `scheduled_batch_success`.
  - Verified the top 10 checked heat-sorted issues return report `success` with
    content. Failed rows from earlier attempts remain for traceability but are
    never served by the API.

### ISS-007: v2 reports hidden by legacy rows and live category filters empty
- **Severity**: High
- **Found**: 2026-07-09
- **Status**: Resolved on `debug/ISS-007-v2-report-category-filter`
- **Reproduction steps**:
  1. Use the configured development DB after `TASK-043`.
  2. Observe `ai_reports` has only `success|v1` rows and
     `/api/issues/{id}/report` returns `not_yet_generated`.
  3. Generate v2 reports and observe rows can share the same metric timestamp
     as v1 rows, so a `generated_at DESC` read can still select legacy content.
  4. Open the dashboard and choose `정치`; the frontend sends
     `category=politics`, while live DB rows store categories such as
     `Politics`, so the list is empty.
- **Root cause**:
  - Report reads and report-regeneration eligibility did not prefer the current
    prompt version when v1/v2 rows tied on timestamp.
  - `/api/categories` returned a static sample list instead of categories from
    live servable issues.
  - `/api/issues` category filtering used exact case-sensitive string equality.
- **Impact**:
  - The detail report card could remain empty after v2 rows were generated.
  - Category buttons could point at values that did not match live rows.
- **Fix completed**:
  - `/api/issues/{id}/report` now requests only current `PROMPT_VERSION`
    report rows; legacy rows are preserved but not served.
  - `ai_report_batch` prefers current-version successful rows when determining
    freshness, preventing repeated regeneration for same-timestamp v1/v2 rows.
  - `/api/categories` now returns broad Korean categories derived from
    currently servable live issues, falling back to the broad Korean sample
    list only in DB-free/failure mode.
  - `/api/issues` category filtering accepts those broad Korean labels and
    remains compatible with raw stored category values.
  - Frontend card-level topic labels remain detailed, so issue cards can still
    show labels such as `우크라이나 전쟁` or future `이란 전쟁` while the top
    filter stays under `세계`.
  - Ran guarded reports-only generation three times against the configured
    local/dev DB. Final checked state: `success|v2|30`, and the default
    top-20 heat-sorted issues all have current v2 report content.
