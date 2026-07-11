# TASK-111: V7 validation relaxation and development regeneration

Date: 2026-07-11  
Branch: `data-ai/TASK-111-v7-validation-relax`  
Status: Complete

## Change

- Removed the section-local numeric-token blocker from both generation-time
  acceptance and read-time reconstruction.
- Kept strict JSON shape, exact evidence-reference existence, source-parent
  linkage, prohibited-language filtering, and authored-URL blocking.
- Added those remaining hard requirements directly to the v7 system prompt.
- Advanced the fingerprinted policy version to
  `v7-positive-evidence-2`; the public report version remains `v7`.

## Verification

- Full Backend: 446 tests passed.
- Ruff: passed.
- Diff check: passed.
- Regression coverage proves an authored number absent from evidence is no
  longer a generation or read-time blocker.
- Existing structure, reference, source-parent, language, and URL regressions
  remain passing.

## Development regeneration

- Target: the latest user-requested market that previously failed numeric
  validation, `Will MegaETH perform an airdrop by December 31, 2026?`.
- Provider calls: one approved OpenRouter writer call.
- Result: succeeded on attempt one.
- Request: `7ec1de64-1d76-4ad4-b829-5df8a52fe7fd`.
- Report: `3480ee09-831c-4485-89ac-ef06af48d5d3`.
- Observed writer cost: USD 0.011714.
- Stored reconstruction passed under `v7-positive-evidence-2`.
- Actual report API returned HTTP 200, `status=fresh`, four sections,
  `cache.state=fresh`, data-as-of, and caution content.

No context-research call, production write, deployment, infrastructure change,
schema change, dependency change, or public response-shape change occurred.
One successful regeneration resolves the immediate zero-report condition but
does not by itself authorize TASK-109 legacy deletion or deployment.
