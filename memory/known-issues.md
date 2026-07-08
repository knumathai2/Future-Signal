<!--
Purpose:        Track known bugs, technical debt, and temporary workarounds
Owner:          Debugger / Reviewer
Update Trigger: New bug found, issue resolved, new tech debt identified
Harness Version: 1.1
-->

# Known Issues — Outlook Signals

_Last updated: 2026-07-07_

## Active Bugs

| ID | Severity | Description | Found | Owner |
|----|----------|-------------|-------|-------|
| — | — | (none — implementation not yet started) | — | — |

## Technical Debt

| ID | Description | Impact | Target Resolution |
|----|-------------|--------|-------------------|
| — | (none yet) | — | — |

## Resolved

| ID | Description | Resolved | Method |
|----|-------------|----------|--------|

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
