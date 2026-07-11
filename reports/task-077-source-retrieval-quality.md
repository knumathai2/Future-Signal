# TASK-077 — v5 summary format and source-retrieval quality

_Date: 2026-07-11 · Status: Complete_

## Outcome

- Replaced the interim v5 prose fields with the user-approved contract:
  `executive_summary`, `current_data_interpretation`, three or four
  `conditional_scenarios`, `factors_to_check`, `signals_to_watch`, and nullable
  `evidence_synthesis`.
- Added typed scenario/check/watch items, explicit conditional-language checks,
  unsupported-number rejection, issue-specific lead-section validation,
  duplicate-section checks, deterministic safety sections, and exact evidence
  references.
- Search anchors now prioritize title-derived people, institutions, countries,
  tracked conditions, review dates, and configured official domains. Generic
  stored guidance text cannot become a search entity or condition anchor.
- Polymarket, Kalshi, PredictIt, Metaculus, and Manifold market/forecast pages
  are deterministically rejected as public evidence. Existing official-single-
  source and independent-two-source rules remain unchanged.

## Development evaluation

The TASK-065 baseline had 80 context runs, seven rejected candidates, and zero
verified candidates. A guarded five-target run after the first query revision
completed five normal `no_candidate` rows at USD 0.1322439. Audit found generic
stored condition text entering three queries, so the query builder was corrected
and the eligible slice was rerun. Two fresh rows completed normally at USD
0.04832615; their queries used the actual titles/entities (`Abstract`,
`Israeli`) and condition terms. No publication threshold was relaxed.

| Measure | Result |
|---|---:|
| New completed research rows | 7 |
| New failed research rows | 0 |
| Annotation results inspected | 84 in the first slice; 29 in the fresh corrected slice |
| New candidate drafts | 0 |
| New verified/public candidates | 0 |
| TASK-077 research cost | USD 0.18057005 |
| DB-recorded cumulative program cost | USD 3.09164205 |
| Final total context runs | 87 |
| Final candidates | 7 rejected, 0 verified, 0 withheld |

The zero-source result is valid: no article or official document met the same-
window entity/condition and source-independence requirements. TASK-080 must
therefore include both the real no-source state and, only if later research
produces verified rows, exact stored source links. It must not manufacture a
source-card example from unverified results.

## Verification

- `ruff check app tests`: pass
- Backend full suite: 331 passed
- Added regression coverage for the exact six-field contract, 3–4 conditional
  scenarios, unsupported numbers, generic lead text, entity/condition query
  anchors, generic-condition fallback, and market/forecast-page rejection.
- Previous successful reports remain untouched when v5 validation fails.

