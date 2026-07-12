# Document retention manifest

Date: 2026-07-12
Task: TASK-122
Branch: `pm/TASK-122-document-consolidation`

## Purpose

Keep the active v8 product, safety, API, and operating guidance easy to find
while removing temporary coordination artifacts already preserved in Git
history and summarized by the permanent ledgers.

This manifest covers the approved seven-phase cleanup. Git remains the archive
for removed coordination and superseded implementation detail.

## Retention classes

| Class | Meaning |
|---|---|
| `KEEP` | Active source of truth or required approval, safety, evidence, cost, migration, or decision history |
| `CONSOLIDATE` | Move accurate operating guidance into a canonical README, repair references, then remove the redundant file |
| `DELETE` | Temporary coordination artifact whose durable outcome is already recorded elsewhere and remains recoverable from Git |
| `REVIEW_LATER` | Potentially redundant, but outside the first three phases or requiring content-level judgment |

## KEEP

- `AGENTS.md`, `standards.md`, and `memory/glossary.md`;
- `docs/prd/**`, `docs/service-design/**`, `docs/tech-design/**`, and
  `docs/ux-design/**`;
- `memory/decisions.md`, `tasks/completed.md`, and migration documentation;
- `docs/archive/ai-report-contracts/README.md`;
- provider-cost, database-application, approval, safety, evidence, and current
  v8 task reports;
- `reports/task-040-demo-script-deck-draft.md` as the presentation artifact;
- current code, configuration examples, migrations, and generated API schema.

## DELETE

- all 76 archived handoffs under `memory/sessions/*.md`; the live handoff stays
  in `memory/session.md`;
- all 10 completed hackathon coordination records matching
  `reports/day-*.md`;
- all six completed review notes matching `reports/review-*.md`;
- `reports/task-040-demo-script-deck-draft-prompt.md`;
- `reports/task-051-v3-report-cards-prompt.md`.
- task reports that only restated implementation later captured by the active
  v8 contract, canonical design documents, tests, or retained integration
  reviews.

The permanent task, roadmap, decision, and project ledgers retain the durable
outcomes. References to removed artifacts must be rewritten as historical
plain text or redirected to a retained canonical record.

## CONSOLIDATE

- replace the empty root `README.md` with the project entry point and canonical
  document map;
- update `frontend/README.md` to the actual package scripts and remove the
  obsolete TASK-005/deployment claim;
- keep current Backend commands in `backend/README.md` and clarify the normal
  v8 on-demand path versus historical compatibility commands;
- remove `commands.md` after eliminating its nonexistent module, migration,
  seed, and workflow paths;
- remove `tech-stack.md` because Technical Design is the authoritative and
  more current stack record.
- compact `memory/session.md`, `memory/project.md`, `memory/known-issues.md`,
  and `memory/architecture.md` to current operating state;
- keep the active v8 contract in `backend/API_CONTRACT.md` and route v1-v7
  history to `docs/archive/ai-report-contracts/README.md`;
- collapse superseded v4-v7 implementation walkthroughs in Service,
  Technical, and UX Design while retaining permanent safety constraints;
- replace stale backlog allocation history with current release, reliability,
  and maintenance work.

## Retained report evidence

The retained report set includes:

- approval packets and binding program boundaries;
- provider cost and bounded-evaluation records;
- database application and cleanup evidence;
- wording, provenance, evidence, contradiction, and failure-mode reviews;
- the current v8 prompt, source retrieval, streaming, integration, and
  acceptance reports;
- the demo artifact and the TASK-122 consolidation review.

Removed implementation summaries remain recoverable from Git. Immutable ADR
and completed-task text may therefore contain literal paths to retired files.

## Required verification

- no active Markdown link points to a removed document; historical audit text
  may retain a literal retired path when changing it would rewrite the record;
- no retained setup guide names a missing command, module, or workflow;
- root, Frontend, and Backend setup instructions match checked-in scripts;
- safety wording and approval policy remain unchanged;
- `git diff --check` passes;
- no source code, API contract, schema, database, provider, infrastructure, or
  deployment state changes in this cleanup.
