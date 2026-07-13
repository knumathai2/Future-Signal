<!--
Purpose:        Current session handoff only
Owner:          Currently active agent
Update Trigger: Every session
Harness Version: 1.1
-->

# Current Session — Outlook Signals

_Last updated: 2026-07-13_

Git history preserves earlier session states; do not create per-session archive
files.

## Session

- **Role**: Backend Implementer
- **Branch**: `backend/TASK-137-category-visibility`
- **Goal**: Remove sports and catch-all labels from public category navigation
  without deleting source data.
- **Status**: TASK-137 complete; latest main deployment and data-refresh handoff preserved

## Completed in TASK-137

- Limited `/api/categories` to the five approved public navigation groups:
  `정치`, `경제`, `환경`, `기술`, and `세계`, returning only groups with
  currently servable issues.
- Kept sports and catch-all issue rows in storage and in the unfiltered issue
  list; existing direct category matching remains available for compatibility.
- Mapped stablecoin, Tether, USDC, and USDT topics to `경제`, so the current
  USDT issue no longer falls into the catch-all group.
- Confirmed the configured local database now derives the visible category
  response `정치`, `경제`, `기술`, `세계`; no category was fabricated for the
  currently empty `환경` group.
- Passed Ruff, focused 79 API tests, all 548 Backend tests, and Frontend
  typecheck, lint, and production build. The known Recharts bundle-size warning
  remains unchanged.
- No schema, dependency, database write, provider call, infrastructure,
  deployment, production action, or wording-policy change occurred.

## Completed in TASK-136

- Added one dependency-free neutral spinner component with a reduced-motion
  fallback.
- Added visible progress to briefing request submission and queued/running
  generation while preserving validated-block streaming and the existing
  caution/timestamp surface.
- Added visible progress to scenario session loading, question submission, and
  pending validated response blocks.
- Added an immediate ref-backed submission guard so a repeated click or Enter
  cannot start a second turn while the first POST is still awaiting its queued
  response.
- Fixed the first-question transition so the empty prompt disappears while the
  turn POST is pending and an in-transcript loading state remains visible until
  the queued user turn and response placeholder replace it.
- TASK-136 itself made no provider, feature-activation, API, schema, database,
  dependency, infrastructure, deployment, production, or wording-policy change.
- Passed Prettier, typecheck, lint, report/scenario parser checks, production
  build, changed-string wording scan, and local Browser verification. The known
  Recharts bundle-size warning remains unchanged.

## Completed in approved production activation

- Added guarded production execution for on-demand v8 briefing and scenario
  workers; local/development defaults remain unchanged.
- Production Compose now passes the existing provider credential reference
  without printing or modifying the secret, enables both generation workers
  and scenario sessions, and was rebuilt/restarted successfully.
- Confirmed production DB already contained migrations 005 and 006; no migration
  write was needed.
- Recovered the previously queued briefing request; one validated v8 report was
  stored and public GET returned `fresh`.
- Created, processed, streamed, and deleted one production scenario session
  after a final successful writer evaluation.
- Early bounded scenario probes failed closed on `unsupported_number` and
  `unconditional_model_premise`; the deterministic input-date allowance and
  prompt restrictions were added before the successful final probe.

## Completed in server restart and DB-path recovery

- Rebuilt and recreated both Compose services under the user's deployment
  approval; both containers report healthy.
- The first restart exposed the honest static fallback because Backend was
  attached only to Docker's internal network and could not resolve Supabase.
- Added a separate outbound `egress` network to Backend while keeping its port
  unpublished and preserving the internal Frontend-to-Backend `app` network.
- Container-side `SELECT 1`, local gateway health, and public HTTPS health pass.
- Local and public `/api/issues` now both return 20 rows with `data_as_of`
  `2026-07-13T02:52:01.754303Z`; no OpenRouter call or schema change occurred.

## Completed in local market-data refresh

- Ran the approved collection-only live Gamma path against the configured local
  development database with a 50-sample ceiling.
- Appended 50 snapshots and 50 metrics, moving the latest data timestamp from
  2026-07-12 21:09:15 UTC to 2026-07-13 02:52:01 UTC.
- Recorded two new expectation-shift signals; three duplicate signals were
  correctly suppressed by the cooldown and no sample failed processing.
- `/api/issues` returned 20 rows with top-level `data_as_of` at the new timestamp.
- AI reports and context research were explicitly skipped, so no OpenRouter call
  occurred. No schema, dependency, deployment, or production change occurred.

## Completed in local end-to-end verification

- Added root and nested `.env` exclusions to `.dockerignore`; the Backend build
  context dropped from about 598 kB to 2.35 kB and both images rebuilt.
- Recorded the user's removal of the previous provider-call count ceiling for
  purpose-bound local/development verification under the existing USD 100 cap.
- Confirmed the configured database and OpenRouter-compatible credential load
  without printing a value, and completed a read-only connection check.
- Passed Ruff and all 546 Backend tests plus every Frontend parser, typecheck,
  lint, and production-build check.
- Confirmed all current issue detail/history GET paths return 200.
- The first briefing request failed closed before a provider call because its
  latest metric lacked complete research input. A context-ready unused issue
  then completed research and writer generation, stored six validated blocks,
  and returned a fresh public briefing.
- One scenario call completed, stored the validated assistant turn and three
  blocks, and reconstructed two turns plus one premise through the public API.
- Stored usage recorded USD 0.06948625 for context research, USD 0.0097225 for
  the briefing writer, and USD 0.006077 for the scenario writer: USD 0.08528575
  total for this verification.
- No deployment, production write, migration, schema/dependency/API change,
  secret mutation or output, production scenario activation, or wording-policy
  change occurred during that local verification stage.

## Completed in TASK-021 so far

- Reviewed the final user-provided 14-slide deck `2팀 발표a.pptx` at full size
  and produced `outputs/2팀_발표대본.md`, a roughly 7.5-minute Korean script
  with slide transitions, a 45-60-second demo cue, a live-demo fallback, a
  one-page cue sheet, and rehearsal notes.
- Produced an editable 14-slide PowerPoint covering the user problem, public-
  data insight, product flow, dashboard/detail experience, validated-block
  briefing boundary, product safeguards, architecture, implementation evidence,
  and closing message.
- Added a dedicated 16:9 demo-video placeholder immediately after the four-step
  user flow. Its adjacent cues cover home discovery, detail chart/briefing, and
  interpretation caution plus conditional conversation before later slides
  explain those scenes individually.
- Added a separate scenario-conversation slide that keeps the default-off local
  boundary distinct from the current briefing, and a four-person team slide
  with blank name lines. PM is shown as the overall coordinator and helper who
  also owns review, wording/safety inspection, and integrated debugging.
- Used three stored project UI captures without presenting the default-off
  scenario conversation as an active core feature.
- Matched the current warm neutral, terracotta, and muted-blue UI direction and
  kept data timing and interpretation caution visible in the product story.
- Rendered and inspected every slide individually, corrected the time-series
  visual, and passed the automated overflow check with no layout overflow.
- Preserved the earlier decks and saved the current revision as
  `outputs/outlook-signals-presentation-v3.pptx`.
- No provider call, dependency, schema, API, infrastructure, deployment,
  production write, or wording-policy change occurred.

## Completed in TASK-135

- Kept complete-output validation and persistence as the public safety boundary;
  raw provider chunks are still never sent to the browser.
- Changed authenticated scenario SSE replay to send the first stored block
  immediately and subsequent paragraph/list blocks at 0.2-second intervals.
- Materialized plain event payloads and rolled back the read transaction before
  paced delivery, so a slow client does not retain a database connection.
- Added a three-block regression for event count, sequence order, timing, final
  completion, and capability non-disclosure.
- Passed Ruff, the focused 15 scenario API tests, all 546 Backend tests, and
  Frontend typecheck, lint, build, and scenario parser checks.
- No provider call, database write, migration, dependency, deployment,
  production action, activation, or wording-policy change occurred.

## Completed in TASK-134

- Reduced the default PostgreSQL pool per API/worker process to three persistent
  plus one overflow connection, with bounded timeout and recycle settings.
- Added five-second attempt-zero queued detection on authenticated status and
  SSE reads, plus a 20-second cooldown and maximum three child launches per
  process.
- Added a row-locked request claim so concurrent children cannot duplicate a
  provider call; running and terminal attempts remain ineligible for recovery.
- Passed Ruff, 44 focused tests, and all 546 Backend tests.
- Restarting the local server automatically recovered the preserved queued
  request through its original browser connection without manual worker launch.
- Exactly one OpenRouter call used 1,312 input and 784 output tokens, cost USD
  0.00634325, and stored one assistant turn plus three validated blocks.
- No second call or retry occurred, and the pool-ceiling error did not recur.

## Completed in TASK-133

- Created one new local ephemeral session and immutable request through the
  TASK-129 Frontend and TASK-132 automatic worker path.
- Consumed exactly one approved OpenRouter call using `openai/gpt-5.6-luna`:
  1,147 input tokens, 832 output tokens, USD 0.006425.
- Writer version 2 passed every validation gate and stored one assistant turn
  plus three complete paragraph blocks; no retry or second call occurred.
- Authenticated SSE completed, the Frontend rendered the conditional response
  with timing/caution, and same-tab reload reconstructed it from storage.
- Browser console verification returned zero errors.
- A concurrent report reload briefly hit the Supabase session-mode 15-client
  ceiling and safely fell back; TASK-134 later closed ISS-023 with bounded
  per-process pooling and a successful recovery run.

## Completed in TASK-132

- Added a local/development-only detached worker launcher after a newly created
  scenario turn commits; idempotent replay does not launch a duplicate.
- Kept provider construction and response persistence outside the API process,
  with the default-off flag and production guard unchanged.
- Consumed exactly one approved OpenRouter call using `openai/gpt-5.6-luna`:
  1,141 input tokens, 744 output tokens, USD 0.0058895.
- The response failed closed with `unsupported_number`; no assistant turn,
  premise, or response block was stored and no retry was attempted.
- Found and fixed ordered-list indices being treated as factual numbers. Writer
  version 2 validates parsed paragraph/list content and still rejects unsupported
  numbers inside the actual prose or list items.
- Added a safe Frontend failure message and passed Ruff, 542 Backend tests,
  Frontend formatting/typecheck/lint/build, and the scenario parser regression.

## Completed in TASK-129

- Added the fifth query-linked `시나리오 대화` detail tab without nesting it
  inside the active-v8 briefing.
- Added strict session, turn, status, and block parsers plus inert paragraph/list
  rendering that never activates model-authored HTML, links, images, or media.
- Kept the bearer capability only in memory and sessionStorage, never in a URL,
  and added same-tab recovery, authenticated fetch-SSE cursor replay, polling
  fallback, expiry, stale, rate, failure, limit, and owner-deletion states.
- Preserved data-as-of timing, caution, premise labels, fixed eight-turn and
  1,000-character limits, 44px controls, keyboard tabs, and 320px layout.
- Browser QA created, queued, recovered, and deleted one local test session and
  turn. No scenario writer or provider call was launched.
- Passed Frontend Prettier, typecheck, lint, production build, API/report/scenario
  parser suites, Backend Ruff, and 34 focused scenario tests.

## Completed in TASK-128 so far

- Applied migration 006 to the configured `ENV=local` database and verified six
  scenario tables plus 29 constraints.
- Implemented a single-call, tool-free writer over one issue's reconstructed v8
  evidence, typed premises, and bounded same-session turns.
- Added Unicode/control normalization, premise/source-parent checks, current-
  turn binding, prohibited-language/leakage/number gates, restricted Markdown,
  complete block persistence, usage audit, and guarded CLI execution.
- Fixed the actual PostgreSQL parent insertion order exposed before the call.
- Passed 34 focused scenario tests, all 536 Backend tests, Ruff, and diff checks.
- Used two explicitly approved OpenRouter calls: 2,704 input tokens, 1,397
  output tokens, USD 0.0117605 total. They failed closed on the initial
  assumption-framing detector and then ISO-date number normalization; zero
  assistant turns and zero response blocks were stored. Both corrections are
  now covered by regression tests.

## Boundaries

- TASK-136 is Frontend-only and does not authorize or perform a provider call,
  feature activation, API/schema change, database action, infrastructure change,
  deployment, or production write.
- The presentation uses stored project evidence only; it does not authorize or
  imply a provider call, deployment, production write, feature activation, or
  infrastructure change.
- The merged main history includes a separately approved guarded production
  activation; TASK-136 does not broaden that authorization or runtime scope.
- TASK-021 is not complete until the live-demo rehearsal and backup capture
  sequence are finished.

## Next handoff

TASK-136 loading feedback and its first-question transition follow-up are
complete. The latest main deployment, production-activation, and data-refresh
records are preserved in this handoff.

Use the final user-provided `/Users/sonmyeong-gwan/Desktop/2팀 발표a.pptx`,
which has the four names filled, insert the final 16:9 demo video on slide 5,
select the final demo issue, then rehearse with `outputs/2팀_발표대본.md` and
capture the ordered screenshot/video backup. TASK-130 and TASK-131 remain
separate scenario evaluation and activation work.
