<!--
Purpose:        Current project state snapshot
Owner:          All agents (read), PM / Backend Implementer (write)
Update Trigger: Milestone or active-state change
Harness Version: 1.1
-->

# Project: Outlook Signals

_Last updated: 2026-07-12_

## Summary

Outlook Signals is an issue-monitoring dashboard built from public aggregate
Polymarket data. It presents reflected expectation values, observed changes,
time-series history, evidence-bounded briefings, data timestamps, and
interpretation cautions. It does not assert future results or attribute a
movement to an external event without accepted source support.

## Current state

- **Product**: React issue discovery/list/detail/methodology flow with four
  question-led detail tabs and responsive 320px support.
- **Market data**: Gamma collection, CLOB history support, append-only
  snapshots/metrics/signals, and honest static fallback states.
- **Schedule**: `.github/workflows/four-hour-collection.yml` runs market-data
  collection at minute 17 every four UTC hours. It receives no AI credentials
  and skips context research and briefing generation.
- **Briefing**: Active v8 on-demand worker with strict evidence reconstruction,
  validated NDJSON blocks, SSE replay, polling fallback, cache fingerprints,
  and last-known-good behavior.
- **Database**: Migrations 001-005 are applied only to the approved local
  development database. Production writes and deployment remain unapproved.
- **Documentation**: TASK-122 phases 1-3 are complete and reviewed; phases 4-7
  are active on `pm/TASK-122-document-consolidation`.

## Implementation snapshot

| Area | Active implementation |
|---|---|
| Frontend | TASK-118~120: four detail tabs, shared navigation, restrained terracotta current-context emphasis, muted-blue comparison styling, accessibility and responsive QA |
| API | Market-scoped issue/history/report reads; append-only generation-request POST; request status and validated-block SSE endpoints |
| Collection | TASK-121: collection-only GitHub Actions workflow every four hours; no scheduled provider stage |
| Data | Append-only snapshots and metrics, fixed 24h/7d changes, caution levels, ±5pp signal detection, guarded historical seed |
| Briefing | TASK-112~117: v8 issue-centered prompt, source refinement, safe retry, contextual wording, validated-block streaming |
| Safety | Aggregate-only data, deterministic evidence/source/timestamp checks, exact caution handling, prohibited-language validation |

## Active issues

- **ISS-017**: a queued on-demand request can remain without a worker after a
  process loss. Existing lease recovery covers expired running attempts, not
  every orphaned queued state.
- **ISS-018**: the configured v8 research model may return no standard citation
  annotations, producing a valid zero-source result but limiting source yield.
- **TD-001**: the Frontend production build retains the known Recharts bundle-
  size warning.

Full active technical debt is in `memory/known-issues.md`.

## Current constraints

- `AGENTS.md`, `standards.md`, and `memory/glossary.md` remain binding.
- Every data-bearing screen retains data-as-of timing and interpretation
  caution.
- Normal market collection does not invoke context research or the writer.
- The API does not call Polymarket or an AI provider directly; it may append
  generation request/event state.
- Provider calls, schema changes, dependencies, infrastructure, deployment,
  production writes, and wording-policy changes require their recorded gates.
- Existing migrations and accepted ADR/completed-task text are immutable.

## Recent changes

| Date | Change |
|---|---|
| 2026-07-12 | ISS-020 hardened public source URLs, IPv6 canonicalization, exact Frontend source links, detail-tab query normalization, and report path encoding. |
| 2026-07-12 | TASK-122 phases 1-3 removed temporary coordination artifacts, consolidated setup guidance, restored immutable audit text after review, and passed 488 Backend tests plus all Frontend checks. |
| 2026-07-12 | TASK-121 replaced the retired daily combined workflow with four-hour market-data-only collection and no provider configuration. |
| 2026-07-12 | The approved local cleanup removed stored v1-v7 reports and v7 request history while preserving active v8 rows and reconstruction. |
| 2026-07-12 | TASK-118~120 completed the four-tab detail structure and shared visual/navigation alignment. |
| 2026-07-11 | TASK-117 activated validated-block SSE and preserved polling plus last-known-good fallbacks. |
| 2026-07-11 | TASK-112~116 activated the current v8 evidence, source, retry, and wording boundaries. |

## Next

Complete TASK-122 phases 4-7, then review ISS-017 and ISS-018 separately.
Another provider evaluation, workflow dispatch, deployment, or production
operation requires its own authorization.
