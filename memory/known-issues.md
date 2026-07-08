<!--
Purpose:        Track known bugs, technical debt, and temporary workarounds
Owner:          Debugger / Reviewer
Update Trigger: New bug found, issue resolved, new tech debt identified
Harness Version: 1.1
-->

# Known Issues — Outlook Signals

_Last updated: 2026-07-08_

## Active Bugs

| ID | Severity | Description | Found | Owner |
|----|----------|-------------|-------|-------|
| — | — | (none currently recorded) | — | — |

## Technical Debt

| ID | Description | Impact | Target Resolution |
|----|-------------|--------|-------------------|
| TD-001 | Frontend production build reports a chunk-size warning, likely from Recharts in the first bundle. | Non-blocking for the MVP; initial load could be optimized later. | Consider lazy-loading the detail/chart route after MVP flow stabilizes. |
| TD-002 | `npm audit` reports Vite/esbuild dev-server vulnerabilities when frontend dependencies stay within the approved Vite 5.x major range. | Dev-server security warning; clearing it requires a Vite major upgrade that needs human approval. | Temporarily accepted for PR #6 by ADR-010; revisit in a dependency-maintenance task with explicit Vite major-upgrade approval and manual demo-flow retest. |
| TD-003 | Backend dependency install fails on this machine's default Python 3.9 because the pinned `psycopg[binary]==3.2.3` binary package is not available for that local runtime/platform combination. | A new contributor using default `python3` may be blocked before running backend tests. | Use Python 3.11 for local setup, as documented in `backend/README.md`; later decide whether to formalize a minimum Python version in backend tooling. |
| TD-004 | `backend/API_CONTRACT.md` still contains stale "draft/open item" wording for the report-empty response even though ADR-008 accepted `200 {"status": "not_yet_generated"}`. | Low implementation risk, but it can confuse Day 2 backend/frontend integration if read literally. | Clean up the contract wording during `TASK-010` while preserving the accepted public response shape. |

## Resolved

| ID | Description | Resolved | Method |
|----|-------------|----------|--------|
| DQ-001 | API no-report-yet response shape needed PM/Frontend sign-off. | 2026-07-08 | ADR-008 accepted `200 {"status": "not_yet_generated"}` as the canonical response. |

## Open Design Questions Carried From Planning Docs

Not bugs, but unresolved decisions that will surface as real blockers during the build — resolve these on Day 1–2, don't let them idle:

- Category taxonomy: Polymarket's own tags vs. manual mapping (PRD §20.4, Service Design §12.1)
- Minimum volume/liquidity floor: exclude from ranking entirely vs. badge as low-confidence (PRD §20.5, Service Design §12.2)
- Inflection-point threshold: fixed ±5pp vs. volatility-adjusted (PRD §20.6)
- Confidence/caution badge: single composite score vs. separate qualitative badges (Service Design §12.4, UX Design §14.2)
- Static-JSON fallback path finalization for API failure during the live demo (PRD §20.9, Technical Design §12 "demo script + fallback data")
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
