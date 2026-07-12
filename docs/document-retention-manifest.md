# Document retention manifest

Date: 2026-07-12
Task: TASK-122
Branch: `pm/TASK-122-document-consolidation`

## Purpose

Keep the active v8 product, safety, API, and operating guidance easy to find
while removing temporary coordination artifacts already preserved in Git
history and summarized by the permanent ledgers.

This manifest covers only the first three approved cleanup phases. It does not
compact current memory, API, Service Design, Technical Design, UX Design, task
reports beyond the named prompt drafts, or historical AI contract records.

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

## DELETE in phase 2

- all 76 archived handoffs under `memory/sessions/*.md`; the live handoff stays
  in `memory/session.md`;
- all 10 completed hackathon coordination records matching
  `reports/day-*.md`;
- all six completed review notes matching `reports/review-*.md`;
- `reports/task-040-demo-script-deck-draft-prompt.md`;
- `reports/task-051-v3-report-cards-prompt.md`.

The permanent task, roadmap, decision, and project ledgers retain the durable
outcomes. References to removed artifacts must be rewritten as historical
plain text or redirected to a retained canonical record.

## CONSOLIDATE in phase 3

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

## REVIEW_LATER

- compact `memory/session.md`, `memory/project.md`,
  `memory/known-issues.md`, and `memory/architecture.md`;
- retain only the current v8 contract in `backend/API_CONTRACT.md` and link
  historical contracts to the archive;
- collapse v4-v7 implementation history in the Service, Technical, and UX
  Design documents;
- prune redundant task reports only after preserving approval, cost, database,
  safety, evidence, and failure-recovery records.

## Required verification

- no active Markdown link points to a removed document; historical audit text
  may retain a literal retired path when changing it would rewrite the record;
- no retained setup guide names a missing command, module, or workflow;
- root, Frontend, and Backend setup instructions match checked-in scripts;
- safety wording and approval policy remain unchanged;
- `git diff --check` passes;
- no source code, API contract, schema, database, provider, infrastructure, or
  deployment state changes in this cleanup.
