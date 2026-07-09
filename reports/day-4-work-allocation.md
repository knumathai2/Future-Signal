# Day 4 Work Allocation - Outlook Signals

_Date: 2026-07-09_
_Owner: PM / Planner_
_Branch: `pm/TASK-038-day-4-allocation`_
_Git baseline: `origin/main` at `af83f7e` after fetching latest refs_
_Status update (2026-07-09): current `origin/main` tip is now `6d0eb44`
after PR #36 (`TASK-019`) merged. `TASK-041` is added from that baseline to
close the remaining stored-summary generation readiness gap. Follow-up:
`TASK-041` is complete from `origin/main` at `01df91b`; saved summaries still
require a separately approved database-write generation run._

## Summary

Day 4 is assigned around one goal: complete the summary and demo flow without
expanding the hackathon MVP. Day 3 closed the detail/chart/caution path, so Day
4 should add stored template summaries, show them in the detail flow, curate
manual event candidates for the representative issues, and draft the
presentation/demo story.

The latest git baseline includes PR #28, which merged `TASK-037` Day 3
closeout. No active Day 3 work remains. The Day 4 work below opened the next
implementation sequence from `TASK-015`, `TASK-016`, `TASK-018`, and
`TASK-019`, plus two missing Day 4 execution tasks that come directly from PRD
section 14: backend report/fallback readiness and PM deck/demo draft.

## Progress Update (as of `6d0eb44`)

Most implementation work for the Day 4 demo path is merged.

- `TASK-015` (Data/AI) is **completed**: fixed template report generation,
  OpenAI-backed `LLMClient` wiring, strict 5-field schema parsing, and the
  banned-phrase/pattern safety filter are implemented in
  `backend/app/core/ai_report.py` and `backend/app/core/ai_report_batch.py`.
- `TASK-039` (Backend) is **completed**: `/api/issues/{id}/report` now reads
  latest successful `ai_reports` rows in live mode and preserves the accepted
  neutral empty state when no successful row exists.
- `TASK-016` (Frontend) is **completed**: detail views fetch the report endpoint
  and render success, loading, not-yet-generated, and report-fetch failure states
  with nearby data-as-of timing and caution context.
- `TASK-019` (Data/AI + PM) is **completed**: PR #36 added a guarded
  `backend/app/db/seed_related_events.py` path and four manually curated,
  normalized/live-reachable related-event candidates.
- `TASK-041` is **completed**: report prompt inputs now use the latest
  `market_snapshots` row at or before the selected metric timestamp, matching
  historical-seed runs without fabricating values. The configured development
  DB may still have `ai_reports=0` until the separately approved database-write
  generation run is performed.
- `TASK-040` (PM) is **completed**: the deck outline, 3-5 minute demo script,
  fallback narration, Day 5 screenshot/rehearsal checklist, and judge Q&A draft
  are recorded in `reports/task-040-demo-script-deck-draft.md`.

## Day 4 Assignments

| ID | Owner | Branch | Status | First output needed | Handoff |
|---|---|---|---|---|---|
| TASK-038 | PM / Planner | `pm/TASK-038-day-4-allocation` | completed | Day 4 allocation, sequencing, and scope guardrails | All roles use this for Day 4 priorities |
| TASK-015 | Data/AI Implementer | `data-ai/TASK-015-template-report-generation` | completed | Template-constrained report generator and safety filter | Feeds `TASK-041`, `TASK-018`, and demo summary readiness |
| TASK-039 | Backend Implementer | `backend/TASK-039-stabilize-api-fallback` | completed | Existing `/api/issues/{id}/report` reads latest stored successful report while preserving the accepted response shape | Feeds `TASK-041`; also addresses `TD-009`/`TD-010` demo fallback consistency |
| TASK-016 | Frontend Implementer | `frontend/TASK-016-report-display-ui` | completed | Detail summary card consumes the report endpoint and handles not-yet-generated/error states | Ready to display successful stored reports once `TASK-041` closes the generation gap |
| TASK-019 | PM + Data/AI | `data-ai/TASK-019-curated-events` | completed | 3-5 manually curated event candidates for representative demo issues | Feeds `TASK-018` and `TASK-040` |
| TASK-041 | Data/AI Implementer | `data-ai/TASK-041-report-generation-readiness` | completed | Report batch prompt input construction is compatible with historical-seed metric timestamps; approved-only demo-generation notes are documented | Feeds `TASK-018`, `TASK-040`, and Day 4 closeout |
| TASK-040 | PM / Planner | `pm/TASK-040-demo-script-deck-draft` | completed | Presentation deck outline and demo script draft to roughly 70 percent completeness | Feeds Day 5 final presentation and backup rehearsal |
| TASK-018 | PM / Planner | `pm/TASK-018-copy-lint` | assigned | Content-safety lint report across UI strings, templates, report text, event candidates, and deck/demo copy | Final Day 4 safety gate before closeout |

## Recommended Work Order

### First block — done

- Data/AI completed `TASK-015`.
- Backend completed `TASK-039`.
- Frontend completed `TASK-016`.
- Data/AI + PM completed `TASK-019`.

### Readiness block — done

- Data/AI completed `TASK-041` from latest `origin/main` at `01df91b`.
  `build_prompt_inputs_for_market()` in
  `backend/app/core/ai_report_batch.py` now uses the latest snapshot at or
  before the metric run timestamp instead of requiring exact timestamp equality,
  while preserving the no-fabrication rule.
- Tests cover the historical-seed `+1 microsecond` metric timestamp case,
  future-only snapshot rejection, and `run_ai_report_batch` successful report
  insertion with a fake `LLMClient`.
- The provided `OPENAI_API_KEY` may be used for project-scoped report
  generation per ADR-022. Any write to the configured development DB still
  requires explicit user approval for that run.

### Final block

- PM completed `TASK-040` with a compact demo spine: dashboard -> detail ->
  chart -> summary -> caution/notice -> manual context candidate.
- PM runs `TASK-018` after the report template, UI strings, event candidates,
  demo script draft, and `TASK-041` readiness notes are available.
- Reviewer pass stays embedded. Any user-facing string changed during Day 4
  must pass the project wording lint before review.
- Day 4 closes only if the Home -> Detail -> Chart -> Summary path can be
  demonstrated with either live/local data or honest fallback data.

## Day 4 Guardrails

- Do not deploy, modify infrastructure, apply the schema to a shared or
  production database, add dependencies, or change public API shapes without
  human approval.
- Do not call paid external AI APIs without human approval. ADR-022 records the
  OpenAI provider approval, and the 2026-07-09 follow-up clarifies that the
  provided `OPENAI_API_KEY` may be used for project-scoped report generation
  without separate per-run approval.
- Do not add accounts, saved lists, notifications, scheduled reports, team
  sharing, wallet-level features, or automated event matching.
- Do not expand into P1 `/api/signals` feed, full volatility/attention scoring,
  broad UI polish, or setup documentation until the Day 4 P0 path is complete.
- Related event candidates remain manually curated context candidates for the
  demo set only.

## Acceptance Checklist

Day 4 is ready to close only when:

- Stored template summaries exist or can be generated locally after explicit
  database-write approval for the representative issues without open-ended
  analysis.
- The report endpoint serves the latest successful stored summary when present
  and the accepted neutral empty state when absent.
- The detail summary card renders success, not-yet-generated, and error states
  without losing data-as-of timing or interpretation-caution context.
- 3-5 representative issues have manually curated event candidates, or the
  demo script explicitly avoids event-candidate sections for issues without
  them.
- The presentation/demo draft tells the product story clearly and keeps the
  scope framed as issue monitoring.
- A content-safety lint pass is recorded for changed user-facing strings,
  templates, event candidates, and demo copy.
- No P1/P2 feature has entered active scope without explicit PM assignment and
  the required human approval where applicable.

## Stretch Work

Only after the checklist above is satisfied, the team may consider the existing
P1 `TASK-025` empty/loading/error state polish or small responsive fixes that
directly improve the demo path. Do not start category/feed/extra metric work on
Day 4 unless the PM explicitly reassigns scope.
