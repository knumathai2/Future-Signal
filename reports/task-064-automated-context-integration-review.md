# TASK-064 — Automated-context integration review

_Date: 2026-07-11 · Verdict: Approved after one in-scope fix_

## Scope and approval audit

- Reviewed TASK-057~063 against ADR-038 and the TASK-055 execution plan.
- No dependency, infrastructure, deployment, scheduled-workflow, or production
  database change was introduced.
- `001_initial_schema.sql` is byte-for-byte unchanged from the pre-v4 baseline;
  the only new migration is append-only `002_context_candidates.sql` plus its
  documentation.
- The only public contract change is the approved existing report route's v4
  response. API requests remain read-only and never call a provider.
- Provider-capable code shares the approved cumulative USD 100 reservation and
  was exercised here with fake clients only.

## End-to-end evidence

`backend/tests/test_context_integration.py` now executes one complete local,
DB-backed fixture:

1. initial market/snapshot/metric/signal schema rows;
2. bounded research output with an annotation-derived official source;
3. deterministic hard gates and independent no-web verifier;
4. append-only verified candidate and collection-run storage;
5. strict v4 writer with metric/candidate evidence references;
6. read-time reconstruction and approved public API source fields.

The Frontend parser regression then enforces the same top-level, seven-field,
timestamp, evidence-reference, candidate, and source boundary before the
change-episode UI renders it.

## Adversarial matrix

| Case | Expected boundary | Evidence |
|---|---|---|
| URL written only in model body | Never evidence | `test_model_body_url_is_not_evidence_and_candidate_is_filtered` |
| Missing web-search annotation | Fail closed / normal empty where applicable | context-research annotation tests |
| Official direct source | Eligible only after independent verification | `test_official_single_source_passes_hard_gate_and_independent_verification` + integration test |
| Two independent sources | Eligible only with distinct publisher families/content | `test_two_independent_sources_pass_when_domains_and_content_are_distinct` |
| Republished/duplicate content | Not independent | republish spacing/content tests |
| Conflicting source date | Rejected before public output | `test_source_date_conflict_rejects_candidate` |
| Weak entity/condition/date/source match | Rejected or withheld | hard-gate parameterized tests and verifier-disagreement tests |
| Verifier adds names/dates/claims | Withheld | verifier new-claim/date/name tests |
| Writer adds URL, number, or relationship assertion | Filtered before storage | v4 writer adversarial tests |
| Metric text differs from linked metric | Not stored/served | v4 semantic and API metric-mismatch tests |
| Missing/reordered/nonexistent candidate ID | `not_yet_generated` | v4 evidence and nonexistent-ID API tests |
| Candidate is withheld, missing a source, or in another episode | `not_yet_generated` | API candidate integrity tests |
| Source has internal field or URL/domain mismatch | `not_yet_generated` / parser error | Backend API and Frontend parser tests |
| No candidate | Successful report with null context and no context UI | batch, API, parser, and Browser zero-candidate checks |

## Finding and fix

The new full-flow fixture found that SQLite returns timezone-naive values even
for timezone-aware model columns. TASK-061 used that raw snapshot time in the
stored observed-change sentence, while TASK-062 normalized the same value to
UTC before reconstructing it. This made a locally generated valid v4 row fail
closed at the API boundary.

The v4 writer input builder now normalizes snapshot, episode, candidate-event,
and end-date timestamps to UTC-aware values before deterministic assembly.
The integration test proves the corrected local/development path from storage
through API output. PostgreSQL behavior remains unchanged.

## Verification result

- Backend: 311 tests passed; Ruff and `git diff --check` passed.
- Frontend: typecheck, lint, v4 parser regression, production build, and
  changed-file Prettier checks passed. The existing Recharts bundle-size warning
  remains unchanged.
- Content safety: changed user-facing strings and report output passed the
  prohibited English/Korean wording scan; relationship, real-result, and action
  assertions remain mechanically blocked.
- Browser: candidate counts 0/1/3, 320px/375px/desktop, timing, caution,
  source-link attributes, exact candidate/marker IDs, null/error/loading states,
  no horizontal overflow, and no console errors passed.

TASK-065 may proceed only on a confirmed local/development database, within the
remaining cumulative provider budget, with deployment and production writes
still excluded.
