# TASK-122: Document consolidation phases 1-7

Date: 2026-07-12
Owner: PM / Reviewer
Branch: `pm/TASK-122-document-consolidation`
Status: Review

## Scope completed

1. Classified documents with an explicit retention manifest.
2. Removed 76 archived handoffs, 10 daily coordination records, six completed
   review notes, two obsolete prompt drafts, and two redundant root guides.
3. Rebuilt the project entry point and aligned Frontend/Backend operating
   commands with checked-in behavior.
4. Compacted current project, session, architecture, and issue memory.
5. Made the public API and active Service, Technical, and UX guidance
   v8-centered, with v1-v7 detail routed to the historical archive.
6. Removed 30 superseded implementation summaries and reduced the backlog to
   current release, reliability, and maintenance work.
7. Repeated link, wording, scope, Backend, and Frontend verification.

## Result

| Measure | Before | After | Change |
|---|---:|---:|---:|
| Markdown files | 202 | 78 | -124 |
| Markdown bytes | 1,278,899 | 656,309 | -622,590 |
| Deleted files | 0 | 126 | 76 handoffs + 48 reports + 2 root guides |
| New retention/review records | 0 | 2 | +2 |

Thirty reports remain. They preserve approval, cost, database, safety,
evidence, failure, current v8, presentation, and consolidation-review records.

## Verification

- `git diff --check` passes.
- Missing relative Markdown links: 0.
- Added-line wording scan: no prohibited token remains.
- Accepted ADR and completed-task history remains unchanged except for the two
  append-only TASK-122 decisions.
- All changed files are Markdown.
- Backend Ruff and all 488 tests pass.
- Frontend typecheck, lint, v8 parser regression, and production build pass;
  the known bundle-size warning remains.
- No source code, API behavior, schema, database, provider, dependency,
  infrastructure, deployment, production, or wording-policy state changed.

## Review boundary

TASK-122 remains in review until the user accepts the final document diff.
The remote branch is not updated by this task without separate direction.
