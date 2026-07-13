<!--
Purpose:        Current project state snapshot
Owner:          All agents (read), PM / Backend Implementer (write)
Update Trigger: Milestone or active-state change
Harness Version: 1.1
-->

# Project: Outlook AI Signals

_Last updated: 2026-07-13_

## Summary

Outlook AI Signals is an issue-monitoring dashboard built from public aggregate
Polymarket data. It presents reflected expectation values, observed changes,
time-series history, evidence-bounded briefings, data timestamps, and
interpretation cautions. It does not assert future results or attribute a
movement to an external event without accepted source support.

## Current state

- **Product**: React issue discovery/list/detail/methodology flow with four
  question-led detail tabs and responsive 320px support.
- **Categories**: Public navigation exposes politics, economy, environment,
  technology, and world groups only; sports and catch-all labels remain
  internal while stablecoin topics group under economy.
- **Market data**: Gamma collection, CLOB history support, append-only
  snapshots/metrics/signals, and honest static fallback states.
- **Schedule**: `.github/workflows/four-hour-collection.yml` runs market-data
  collection at minute 17 every four UTC hours. It receives no AI credentials
  and skips context research and briefing generation.
- **Briefing**: Active v8 on-demand worker with strict evidence reconstruction,
  validated NDJSON blocks, SSE replay, polling fallback, cache fingerprints,
  and last-known-good behavior.
- **Database**: Migrations 001-006 are applied only to the approved local
  development database. Production writes and deployment remain unapproved.
- **Documentation**: TASK-122 phases 1-7 are complete. All 11 tracked README
  files are localized in Korean and revalidated against the current runtime,
  commands, links, and deployment state.
- **Phase 2 boundary**: TASK-123~125 lock the next summary/scenario policy and
  capability-scoped threat model. TASK-126 implements the approved default-off
  local/development API. TASK-128's guarded writer is implemented; two bounded
  evaluations failed closed. TASK-129 adds the isolated Frontend, and TASK-132
  adds local auto-launch. TASK-133's single post-fix evaluation stored and
  reconstructed the first validated scenario response. TASK-134 adds bounded
  attempt-zero recovery and conservative DB pooling; activation stays gated.

## Implementation snapshot

| Area | Active implementation |
|---|---|
| Frontend | Five detail tabs with an isolated scenario conversation, shared navigation, restrained terracotta current-context emphasis, muted-blue comparison styling, accessibility and responsive QA |
| API | Market-scoped issue/history/report reads; append-only generation-request POST; request status and validated-block SSE endpoints |
| Collection | TASK-121: collection-only GitHub Actions workflow every four hours; no scheduled provider stage |
| Data | Append-only snapshots and metrics, fixed 24h/7d changes, caution levels, ±5pp signal detection, guarded historical seed |
| Briefing | TASK-112~117: v8 issue-centered prompt, source refinement, safe retry, contextual wording, validated-block streaming |
| Safety | Aggregate-only data, deterministic evidence/source/timestamp checks, exact caution handling, prohibited-language validation |
| Scenario boundary | Default-off capability-scoped API and separate UI, guarded tool-free local writer with new-request auto-launch, complete-output safety gates, authenticated stored-block SSE, session recovery, restricted rendering, and 24-hour deletion contract |

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
| 2026-07-13 | TASK-138 changed the product display name to Outlook AI Signals across UI, metadata, project documentation, scripts, tests, and all tracked presentation assets while preserving technical slugs and public/storage contracts. |
| 2026-07-13 | ISS-028 advanced the scenario writer to v5 with an exact current-turn plus market-definition ref array and explicit assumption prefix. All 550 Backend tests passed; one v4 evaluation failed closed at USD 0.006011, and one v5 evaluation cost USD 0.0072395 and stored one assistant turn plus three validated blocks without retry. |
| 2026-07-13 | ISS-027 advanced the scenario writer to v3 with an explicit exact current-turn reference contract and minimum output example. All 549 Backend tests passed, and one purpose-bound local evaluation cost USD 0.0063915 and stored one assistant turn plus three validated blocks without retry. |
| 2026-07-13 | TASK-122 completed documentation consolidation and Korean localization of all tracked README files, with current code/configuration, link, command, wording, Compose, DNS, and public-health verification. |
| 2026-07-13 | TASK-137 removed sports and catch-all labels from public category navigation, retained underlying issues, and grouped stablecoin topics under economy without a schema or data mutation. |
| 2026-07-12 | Migration 006 was applied to the approved local DB. TASK-128 added the guarded tool-free writer; two calls costing USD 0.0117605 failed closed on framing and date normalization with no assistant content stored. |
| 2026-07-12 | TASK-126 implemented the approved default-off local/development scenario API, capability authentication, append-only migration 006 (unapplied), stored-block SSE, limits, and hard deletion without a provider, worker, dependency, or database action. |
| 2026-07-12 | TASK-124/125 locked the next summary/scenario policy and documented the ephemeral capability-scoped threat/API/storage proposal without runtime mutation. |
| 2026-07-12 | TASK-123 documented the approval-ready relaxed-summary and secure scenario-conversation plan without changing active policy or runtime state. |
| 2026-07-12 | ISS-021 connected all Frontend REST and SSE requests to one optional validated API origin while leaving split-origin hosting and Backend CORS unconfigured pending approval. |
| 2026-07-12 | ISS-020 hardened public source URLs, IPv6 canonicalization, exact Frontend source links, detail-tab query normalization, and report path encoding. |
| 2026-07-12 | TASK-122 phases 1-3 removed temporary coordination artifacts, consolidated setup guidance, restored immutable audit text after review, and passed 488 Backend tests plus all Frontend checks. |
| 2026-07-12 | TASK-121 replaced the retired daily combined workflow with four-hour market-data-only collection and no provider configuration. |
| 2026-07-12 | The approved local cleanup removed stored v1-v7 reports and v7 request history while preserving active v8 rows and reconstruction. |
| 2026-07-12 | TASK-118~120 completed the four-tab detail structure and shared visual/navigation alignment. |
| 2026-07-11 | TASK-117 activated validated-block SSE and preserved polling plus last-known-good fallbacks. |
| 2026-07-11 | TASK-112~116 activated the current v8 evidence, source, retry, and wording boundaries. |

## Next

Finish the TASK-021 live-demo rehearsal and backup capture sequence, decide the
remaining TASK-128 closeout, and review TASK-109 legacy-runtime cleanup under
its separate gate. Another provider evaluation, workflow dispatch, deployment,
or production operation requires its own authorization.
