# TASK-065 — Local/development backfill preflight

_Date: 2026-07-11 · Status: Blocked at the approved query-policy boundary_

## Completed safely

- Confirmed `ENV=local`, the previously documented Supabase development host,
  configured OpenRouter credentials, and the cumulative USD 100 program cap
  without printing or modifying `.env` or any secret.
- Applied only `backend/migrations/002_context_candidates.sql` to the configured
  development database. Both new tables were verified afterward; migration
  `001_initial_schema.sql` was not changed or reapplied.
- Added a guarded `--context-max-markets` cap so a local/development backfill can
  remain within the planned 30–50 issue range.
- Added exactly one application-level retry for research schema/provider
  failures and retained token/search/cost usage from failed billed responses.
- Full Backend verification now passes 313 tests plus Ruff and diff checks.

## Live preflight evidence

The configured DB began with 69 issues, 33,538 snapshots, 450 metrics, 134
reports, and no v4 context tables or v4 reports. The migration succeeded.

Preflight and diagnostic calls tested current OpenRouter models from different
families, including the project model, the official server-tool documentation's
`openai/gpt-5.2` example, OpenAI mini models, Google Gemini Flash, and Anthropic
Haiku. The independent verifier remained a different provider family in every
stored batch attempt.

Current stored audit state:

| Measure | Value |
|---|---:|
| Context run rows | 16 |
| Distinct attempted issues | 5 |
| Normal no-candidate runs | 1 |
| Failed runs | 15 |
| Rejected candidates | 2 |
| Verified candidates | 0 |
| Successful v4 reports from the first writer preflight | 2 |
| Recorded research/verifier cost | USD 0.749864 |
| Recorded writer cost | USD 0.029062 |
| Recorded program spend | USD 0.778926 |

Several read-only diagnostic calls occurred outside the scheduled logger while
isolating provider behavior. Their observed per-call costs were cents; using
the configured USD 2 reservation for every diagnostic execution gives a
conservative total well below USD 50, still below the approved USD 100 cap.
No further provider calls should run until the policy choice below is approved.

## Blocking incompatibility

The approved TASK-058 hard gate requires the model-returned `queries` array to
be an exact subset of deterministic metadata-derived suggestions. OpenRouter's
current server-tool documentation states that the model generates the search
query and decides when to search. Live responses therefore often:

- execute a search but report a reformulated query;
- return otherwise valid JSON with that out-of-allowlist query;
- or return a different JSON wrapper after tool use.

The client correctly rejects all three. Across five sampled issues this left no
verified candidate, so the required 30+ completed research runs, URL audit, five
candidate→summary→source demos, and incremental-batch proof cannot be claimed.

## Approval needed to continue

Recommended narrow policy amendment:

1. Keep deterministic metadata-derived query suggestions, maximum one to six
   tool calls, maximum 30 annotations, and all existing candidate hard gates.
2. Permit the OpenRouter server tool to reformulate a suggested query, because
   this is the provider's documented execution model.
3. Store/audit the model-reported query strings and require bounded count plus
   normalized topic/entity overlap with the supplied market metadata instead of
   exact string equality.
4. Continue treating only API `url_citation` annotations as evidence; model
   body URLs, names, dates, metrics, and unsupported claims remain rejected.

This changes the approved query policy and therefore requires explicit human
approval under `AGENTS.md`. Deployment and production writes remain excluded.
