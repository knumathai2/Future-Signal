# Review: TASK-007 Batch Collector Fetch + Normalize

Date: 2026-07-08
Reviewer: Reviewer
PR: #9 `feat(data-ai): TASK-007 batch collector fetch and normalize`
Branch reviewed: `data-ai/TASK-007-fetch-normalize`
Verdict: Request Changes

## Findings

### 1. Normalized artifact does not match the downstream contract

Severity: High

`normalized_samples.json` contains 50 records, but the fields required by
`TASK-008`, `TASK-010`, and the accepted technical design are not available at the
record top level. The artifact is missing top-level `title`, `description`,
`category`, `status`, `outcome_type`, `current_value`, `volume_24h`,
`volume_total`, `liquidity`, `polymarket_condition_id`, `market_created_at`, and
history data fields.

Impact: downstream code would have to re-parse nested `raw_data` and infer schema
fields again, which defeats the normalization handoff and risks inconsistent
mapping.

Fix direction: emit Pydantic-validated normalized records shaped for the accepted
schema/API handoff, keeping raw source payloads separate from display-ready fields.

### 2. Skipped invalid records do not produce structured error details

Severity: High

`collector.py` skips many records through `continue` branches and only logs one
generic warning for unexpected exceptions. The TASK-007 Definition of Done requires
invalid records to be skipped with structured error details instead of failing the
whole run.

Impact: the next implementer cannot tell how many events were excluded for
multi-outcome structure, missing prices, inactive state, date filtering, malformed
JSON, or missing token ids.

Fix direction: collect per-record skip reasons and include them in a run summary or
sidecar artifact suitable for `data_collection_logs.error_detail` later.

### 3. HTTP client dependency needs the approval/runtime path reconciled

Severity: Medium

`backend/requirements.txt` adds `requests==2.31.0`, which is a new runtime package
relative to `origin/main`. `AGENTS.md` requires human approval before adding a new
external dependency. In the current backend venv, importing `requests` also fails
until the dependency set is refreshed.

Impact: the collector is not runnable in the checked-in local backend environment,
and the dependency gate is not documented in this PR.

Fix direction: either record approval for the new package and refresh the runtime
setup, or use an already accepted HTTP client path consistently.

### 4. Style checks fail

Severity: Medium

The PR fails `ruff` for import ordering and line length, and `git diff --check`
reports trailing whitespace in `backend/app/core/collector.py`.

Impact: this breaks the project review checklist and creates avoidable cleanup work
for the next data/backend tasks.

Fix direction: run the backend formatter/linter path and remove trailing whitespace
before requesting another review.

### 5. Committed sample data can trip the wording lint if used as fallback/display data

Severity: Medium

The committed JSON artifact stores raw external descriptions. A content-lint scan
found project hard-block terms inside those raw descriptions. Some hits are source
text or substring edge cases, but this artifact is a plausible fallback/demo input,
so it needs a clear boundary before any UI or summary path consumes it.

Impact: raw source text could leak into product copy and violate the project safety
policy.

Fix direction: store sanitized/display-ready descriptions separately, keep raw text
out of demo/fallback payloads, or add a documented transformation step that prevents
raw source descriptions from shipping to user-facing surfaces.

## Verification

- `backend/.venv/bin/python -m pytest backend/tests` -> 10 passed.
- `backend/.venv/bin/python -m ruff check backend/app/core/collector.py` on the PR
  checkout -> failed.
- `git diff --check origin/main...data-ai/TASK-007-fetch-normalize` -> failed.
- Schema probe over `normalized_samples.json` confirmed 50/50 records missing the
  downstream top-level fields listed above.

## Review Notes

The branch has the right overall intent and does produce a 50-record sample, but it
is not ready to merge because the normalized handoff is not yet normalized enough
for the next Day 2 tasks.
