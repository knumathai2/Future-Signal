# TASK-065 — Local/development context backfill evaluation

_Date: 2026-07-11 · Status: Complete in the approved development scope_

## Scope and safety boundary

- ADR-047 was explicitly human-approved before resumption. Deterministic query
  suggestions remain scope anchors; reported server-tool reformulations must be
  unique, bounded, and share normalized distinctive market topic/entity tokens.
- The six-query, 30-annotation, annotation-only evidence, deterministic gate,
  different-provider verifier, verified-only publication, wording, evidence,
  USD 100, and local/development-only write boundaries remained unchanged.
- Migration 002 was applied only to the configured Supabase development DB.
  No deployment, production DB write, infrastructure change, secret output, or
  existing-migration edit occurred.
- OpenRouter documents that the model generates server-tool queries and may
  decide whether to search. The stable research configuration was
  `x-ai/grok-4.3` with native search; `anthropic/claude-haiku-4.5` remained the
  independent no-web verifier.

## Guarded execution

| Run | Target slice | Completed | Isolated failure | Result |
|---|---:|---:|---:|---|
| bounded backfill | 0–29 | 28 | 2 | 28 normal `no_candidate` |
| bounded continuation | 30–39 | 9 | 1 | 9 normal `no_candidate` |
| bounded continuation | 40–49 | 9 | 1 | 9 normal `no_candidate` |
| regular incremental batch | current top 10 | 9 | 1 | 9 normal `no_candidate` |

The backfill therefore covered exactly 50 deterministic targets and completed
46 distinct issues, exceeding the 30-issue acceptance minimum. Four backfill
targets lacked complete research inputs and failed in isolation. The regular
incremental path completed after the backfill and did not block report writing.

Final development audit state:

| Measure | Value |
|---|---:|
| Context run rows | 80 |
| Normal `no_candidate` rows | 57 |
| Failed rows, including preflight history | 23 |
| Distinct issues with completed research | 46 |
| xAI research rows | 61 |
| Maximum recorded query count | 5 of 6 |
| Maximum annotation result count | 26 of 30 |
| Missing reported-query audits on completed xAI rows | 0 |
| Rejected candidates | 7 |
| Verified/public candidates | 0 |
| Successful v4 report rows | 14 across 13 issues |
| DB-recorded research/verifier/writer spend | USD 3.00263875 |

The seven candidate drafts were rejected by the approved deterministic gates;
sample audited reasons included entity mismatch and event date outside the
review window. Several drafts were market-listing or forecast-page material,
which the prompt now excludes. No threshold or publication gate was weakened
to manufacture a demo candidate.

## Acceptance audit

| Requirement | Evidence | Result |
|---|---|---|
| At least 30 issues researched | 46 distinct completed development issues | Pass |
| Every verified candidate has annotation sources | No candidate reached `verified`; zero source-less public rows exist | Pass, 0/0 public rows |
| Public candidate URL access | No public candidate URL was published | Pass, no URL audit population |
| Metric/evidence-reference mismatch | All latest successful v4 reports independently reconstructed; 0 mismatches | Pass |
| Relationship/result assertion | Full stored v4 safety/semantic rerun; 0 failures | Pass |
| Normal no-candidate state | Five live API/UI samples returned success with null context and mandatory boundary/caution | Pass |
| Approved provider budget | USD 3.00263875 recorded; conservative bound including unlogged diagnostics remains below USD 80 | Pass |
| Five uninterrupted demo flows | Five live no-candidate flows plus five clearly labeled localhost-only candidate fixtures | Pass |

The conservative spend bound preserves the earlier sub-USD-50 diagnostic bound
and adds USD 2 for each later direct diagnostic execution. It remains below the
human-approved USD 100 ceiling even though observed direct-call charges were
only cents.

## API and report proof

Independent reconstruction covered 13 latest successful v4 issue rows:

- evidence-reference mismatches: 0;
- stored safety/semantic failures: 0;
- successful no-context reports: 13;
- five sampled report/detail/history flows: HTTP 200 for every request;
- every sampled report displayed a mandatory caution and every detail response
  carried a data-as-of timestamp.

The v4 writer initially exposed two provider-shape problems: a list-valued
`what_to_check` and unsafe/numeric wording in model-authored fields. The prompt
was tightened without weakening validation: both values must be Korean prose
strings, raw description/data-platform wording is excluded, and digits are
prohibited because deterministic fields already own dates and metrics. The
final stored-context writer batch passed 10 of 10 strict generations.

## Browser evidence

Actual development API no-candidate flows:

1. `fe0bd5bc-5f79-49b4-9b3a-c10bbf070db1`
2. `ca732cff-69e9-4be9-b155-76541aa3108a`
3. `e26a5154-9313-476c-b903-ac959fc2d293`
4. `45786d60-e483-4168-874b-becc944a54af`
5. `6e847e48-99a7-4201-b49a-c86e9e0b1099`

Screenshots: `artifacts/task-065/no-context-01.png` through
`no-context-05.png`. Every flow showed the change episode, relationship
boundary, and caution; the candidate/source region was absent and no report
error was visible.

Candidate UI proof used the existing localhost-only `?report=v4-3` fixture and
is not represented as development DB evidence. It ran on the first three and
fifth issue above plus `79a5ac93-3eb9-4b2a-b5a1-7bfb7ec7284d`, which has enough
chart history. Screenshots: `artifacts/task-065/fixture-candidates-01.png`
through `fixture-candidates-05.png`. Every flow had:

- three candidate cards;
- three exact-ID chart markers and three marker links;
- four source links with `noopener noreferrer`;
- zero report errors.

The first fixture candidate date was moved inside the fixture chart range after
Browser QA found that its marker anchor was otherwise absent. A clean final tab
reported three cards, three markers, and zero console errors. Rapid early
navigation temporarily exhausted the development Supabase session pool; the
serialized clean rerun passed and no production/infrastructure setting changed.

## Verification commands

- Backend: full Pytest suite, Ruff, and `git diff --check`.
- Frontend: typecheck, ESLint, strict report-parser regression, production build,
  and Browser screenshot/console checks.
- Development DB: read-only aggregate audit, v4 input reconstruction, strict
  semantic/safety rerun, and five live API samples.

Official provider references:

- <https://openrouter.ai/docs/guides/features/server-tools/web-search>
- <https://openrouter.ai/docs/guides/features/structured-outputs>
