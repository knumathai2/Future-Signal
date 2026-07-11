# TASK-103: Broad context collection and lightweight evidence classification

Date: 2026-07-11  
Owner: Data/AI Implementer  
Branch: `data-ai/TASK-103-broad-context-collection`  
Status: Complete

## Result

Added a separate v7 context-policy module. The historical v4 strict
verified-only implementation remains unchanged for audit and comparison.

## Broad collection

`broaden_v7_research_inputs()` expands a narrow episode window to a bounded
30-day reusable issue-context window, clears the inflection-only anchor, and
retains exact issue, condition, category, source-domain, and timing metadata.
The existing annotation-only OpenRouter research client still supplies exact
URLs and excerpts; model-body URLs never become evidence.

## A-D classification

- A: exact allowed/official domain with an excerpt-supported claim;
- B: configured established reporting/institution domain with support;
- C: other safe relevant single-source material with support;
- D: disallowed market/forecast domain, inaccessible/empty material, missing
  claim support, unknown annotation, or another deterministic failure.

Only A-C sources expose supported claims. Every claim retains an opaque claim
ref, exact citation ID, exact stored excerpt, source URL/domain/title/hash, and
level. A title can establish relevance but cannot by itself support a factual
claim.

## Conditional verifier

Verifier triggers are source conflict, ambiguous/strong relationship language,
high-impact B/C claims, and a level-C claim selected to materially shape the
summary. An A source with direct deterministic support and no conflict skips
the model call. A triggered candidate fails closed when the verifier is absent.

The no-search verifier receives only exact stored excerpts and claim refs. It
must use a different provider family from research, cannot add a claim ref,
cannot promote D, and can only accept or withhold the already classified
candidate.

## Verification

- Ten v7 policy tests cover A, B, supporting/material C, three D paths,
  conflicts, high-impact claims, missing verifier, independent acceptance,
  same-family rejection, one research call, and 30-day broadening.
- Existing research and strict v4 verifier regressions remain green.
- Combined context verification passes 71 tests; Ruff and diff checks pass.

No live provider call, database write, schema/API/workflow change, dependency,
infrastructure, deployment, or production action occurred.
