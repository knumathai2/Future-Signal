# TASK-122: Document consolidation phases 1-3

Date: 2026-07-12
Owner: PM / Reviewer
Branch: `pm/TASK-122-document-consolidation`
Status: Review

## Scope completed

1. Added `docs/document-retention-manifest.md` with keep, consolidate,
   delete, and later-review boundaries.
2. Removed 76 archived session handoffs, 10 daily coordination records, six
   completed review notes, and two obsolete prompt drafts.
3. Replaced the empty root README, aligned the Frontend README with checked-in
   package scripts, aligned the Backend README with the active four-hour
   market-data workflow and v8 on-demand path, and removed the obsolete
   `commands.md` and redundant `tech-stack.md`.

Current memory compaction, API/design history compaction, and broader task-
report pruning were intentionally not performed.

## Result

| Measure | Before | After | Change |
|---|---:|---:|---:|
| Markdown files | 202 | 108 | -94 |
| Markdown bytes | 1,278,899 | 962,061 | -316,838 |
| Deleted files | 0 | 96 | 76 sessions + 18 reports + 2 redundant root guides |
| New retention/review records | 0 | 2 | +2 |

## Verification

- `git diff --check` passes.
- Missing relative Markdown links: 0.
- No active relative Markdown link points to a deleted document. Immutable
  historical ADR, completed-task, and evidence text may retain a literal
  retired path, whose artifact remains recoverable from Git history.
- `scheduled_batch`, `historical_seed`, and `on_demand_worker` README commands
  import and return `--help` successfully from `backend/`.
- Root README verification commands use independent working directories.
- Backend Ruff and all 488 tests pass.
- Frontend typecheck, lint, v8 report-parser regression, and production build
  pass; the known bundle-size warning remains.
- Historical `memory/decisions.md`, `tasks/completed.md`, TASK-018, and TASK-040
  text matches the pre-cleanup commit exactly. Only new ADR-064 records the
  retirement decision.
- All changed files are Markdown; no source, API, schema, database, provider,
  dependency, infrastructure, deployment, or product wording-policy state
  changed.

## Review boundary

Review the root/Frontend/Backend READMEs, the retention manifest, and the
reference rewrites. Do not start phase 4 memory/API/design compaction until the
user accepts this diff.
