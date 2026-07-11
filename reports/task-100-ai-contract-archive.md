# TASK-100: Constraint inventory and v1-v6 contract archive

Date: 2026-07-11  
Owner: PM / Reviewer  
Branch: `pm/TASK-100-ai-contract-archive`  
Status: Complete

## Outcome

The historical contract index now lives at
`docs/archive/ai-report-contracts/README.md`. It maps v1-v6 to their ADRs,
public shapes, active periods, supersession reasons, current code surfaces, and
retention requirements. V6 remains the current runtime; proposed v7 policy is
not active merely because the archive exists.

## Active constraint inventory

### Constitution-level restrictions

These remain binding across v7 and cannot be treated as legacy prompt baggage:

1. aggregate-only public data;
2. no asserted future result, invented cause, or predictive claim;
3. honest data timing plus interpretation caution on every data screen;
4. no unconstrained or evidence-free authored analysis;
5. no production write, deployment, new dependency, schema change, public API
   change, infrastructure mutation, or wording-policy amendment without the
   required human approval; and
6. no edit of an existing migration or direct commit to the default branch.

### Evidence-integrity blockers

These should remain deterministic blockers in v7:

- unknown, duplicated where uniqueness is required, or mismatched evidence
  references;
- invented or altered source URLs, titles, claims, metrics, dates, entities,
  source levels, or timestamps;
- unsafe URLs or a URL/domain mismatch;
- factual prose that materially conflicts with the referenced stored input;
- an invalid public envelope or a result that cannot be reconstructed;
- a context or report record that violates append-only provenance; and
- provider or validation failure overwriting the last valid report.

### Version-specific constraints eligible for supersession review

These are historical contract choices, not automatically permanent safety
requirements:

- v3's exact eight fields and sentence/character layout;
- v4's two authored fields and universal strict candidate-publication shape;
- v5's exact scenario/check/watch arrays, exact source-title occurrence rule,
  and four-value item basis contract;
- v6's four mode unions, metric/rule single-owner prose rules, general-scenario
  section ownership, authored-date ban, non-anchor English ban, and strict
  section duplication thresholds; and
- scheduled collection-time report invocation.

TASK-101 must explicitly decide which of these are superseded. Until that
approved policy lands, current v6 behavior remains authoritative.

## Runtime inventory

| Layer | Current v6 surface | Historical compatibility present |
|---|---|---|
| Writer | `backend/app/core/ai_report.py` | v3, v4, v5, and v6 builders/checks share the module |
| Batch | `backend/app/core/ai_report_batch.py` and `backend/app/core/scheduled_batch.py` | v3-v6 dispatch and scheduled flags remain |
| Context | `backend/app/core/context_research.py`, `context_verification.py`, `context_research_batch.py` | v4 policy identifiers and strict verifier path remain |
| Storage/read | `backend/app/db/models.py`, `backend/app/db/queries.py` | append-only rows and v4-v6 loaders remain |
| API | `backend/app/api/routes/issues.py`, `backend/app/schemas/issues.py` | current v6 read plus legacy schema types remain |
| Frontend | `frontend/src/types/issue.ts`, `frontend/src/utils/reportParser.ts`, `frontend/src/data/reportFixtures.ts` | v6 is active; historical shapes survive mainly in backend/docs/tests |
| Documentation | `backend/API_CONTRACT.md`, product design docs, ADRs, task reports | mixed current and historical sections require later active-policy cleanup |

## Supersession state

- TASK-097/098 v6 code and evidence remain preserved as the latest implemented
  baseline for comparison.
- The reopened v6 development regeneration is superseded as the next delivery
  priority by the user's TASK-099~109 direction; no additional v6 provider call
  is made by TASK-100.
- V6 remains served until TASK-101~107 activate and verify v7.
- V1-v5 remain audit-only for the current endpoint.
- No file, database row, migration, provider configuration, or runtime path was
  removed or changed in TASK-100.

## Verification

- Archive entries were checked against ADR-003, ADR-028, ADR-030, ADR-033,
  ADR-034, ADR-038, ADR-043~050, current source constants, API documentation,
  Frontend parser/types, and version task reports.
- `git diff --check` passes.
- A focused repository scan confirms the archive contains v1 through v6 and
  the cleanup boundary retains migrations, rows, ADRs, and audit evidence.

## Next gate

TASK-101 is next. It changes the binding AI/wording and automated-context
policy, so implementation must wait for the explicit approval packet recorded
in TASK-099.
