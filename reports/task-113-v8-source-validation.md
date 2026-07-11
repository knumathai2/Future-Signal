# TASK-113: V8 source retrieval and validation improvement

Date: 2026-07-11  
Owner: Data/AI Implementer  
Branch: `data-ai/TASK-113-v8-source-validation`  
Status: Implemented; live source acceptance blocked by ISS-018

## Approved objective

Improve v8 briefing usefulness by widening bounded source discovery and by
accepting excerpt-backed claims across common entity and issue aliases. Keep
the existing fail-closed controls for exact annotation URLs, publisher
identity, non-empty excerpts, source-parent linkage, duplicate/conflict
handling, unsafe domains, unsupported claims, and causal or future-outcome
assertions.

## Implementation boundary

- Select a 90-day or 180-day lookback from the issue horizon and topic.
- Add deterministic query aliases without allowing out-of-scope queries.
- Evaluate source relevance across the source title and exact stored excerpt.
- Allow an excerpt to support a narrowly scoped candidate claim through
  deterministic concept aliases, while retaining the exact excerpt.
- Keep A-C attribution and conditional verification for material C, conflict,
  ambiguity, and high-impact claims.
- Advance the active v8 context policy fingerprint so cached requests do not
  reuse the earlier source policy.

No schema migration, dependency, infrastructure change, deployment,
production write, or legacy deletion is included.

## Outcome

- Added deterministic 90-day and 180-day v8 research horizons.
- Added bounded cross-wording queries and canonical relevance aliases.
- Required excerpt-level topic overlap and used the exact excerpt when broader
  candidate wording was not directly supported.
- Advanced active context policy and cache fingerprints to
  `v8-source-level-2` while retaining historical v7 context rows as valid
  evidence inputs.
- Connected the Frontend briefing action to `refresh_context=true`.
- Lazily connected bounded research and optional independent verification in
  the local/development worker.
- Preserved immutable request fingerprints by following the generated
  successor request after a context refresh changes evidence.
- Added cumulative context-cost reservation checking before research.
- Removed Chat Completions JSON mode from server-tool research requests after
  the configured provider rejected web search combined with
  `response_format=json_object`; strict prompt/schema parsing and one bounded
  retry remain fail-closed.
- Added an annotation-only fallback for successful server-tool responses that
  return natural language instead of the requested JSON. It ignores model-body
  links and constructs narrow candidates only from exact annotation title,
  URL, and excerpt fields before the same relevance/source gates run.
- Set server-tool choice to `required` after live evaluation showed the model
  could otherwise complete twice without performing a web search.
- Treat provider-authored query-audit JSON as optional when exact annotations
  exist: bounded deterministic scope queries remain the audit record and only
  annotation fields can become candidates. Failed calls now persist aggregate
  usage and a fixed, secret-free reason so cumulative budget checks include
  unsuccessful research.
- Keep the server tool as the first research attempt, then use OpenRouter's
  always-on web plugin only for the bounded second attempt when the configured
  model does not execute the server tool. Both paths accept only normalized
  `url_citation` annotations.

## Verification

- Backend: 459 tests passed.
- Ruff: all Backend application and test files passed.
- Frontend: typecheck, lint, v8 parser regression, and production build passed.
- Repository diff check passed.
- The production build retains the known bundle-size warning.

## Development evaluation

The explicitly approved local/development evaluation targeted
`U.S. x Russia Nuclear deal by December 31, 2026?` through request
`539a4e90-1386-4d82-accd-faea26c1c76a`.

- The first provider requests exposed and fixed the live incompatibilities
  recorded above: web search with JSON mode, optional server-tool execution,
  natural-language response handling, current usage-field parsing, and the
  compatibility plugin parameters.
- The final configured-model attempt performed two plugin web searches but
  returned no standard `url_citation` annotations. The pipeline therefore
  failed closed with zero candidates and did not store a new report.
- Eight failed development context-run audit rows were appended. Three rows
  recorded USD 0.22190440 after failure-usage persistence was implemented.
  Two direct diagnostics recorded another USD 0.11140620. Earlier successful
  responses in this evaluation occurred before failed usage was persisted, so
  USD 0.33331060 is a minimum rather than a complete evaluation total; this
  accounting gap is recorded in ISS-018.

No migration, dependency, infrastructure change, deployment, production
action, production database write, or legacy deletion was performed. The only
non-test writes were the explicitly approved development request/event/context
audit rows; no unsupported source or new briefing was stored.
