# TASK-081 — Actual v4/v5 quality review package

_Date: 2026-07-11 · Status: Complete_

## Actual comparison case

Issue: `Israeli parliament dissolved by July 31?`

The latest development v4 report had two authored sections. Its overview used
broad political-stability language not supported by a verified source, while
its checklist broadly suggested reviewing announcements, schedules, and public
statements. It did show the correct deterministic 89.5%, +10.5pp, and +19.5pp
movement section and mandatory caution.

The final v5 report keeps the exact market title in the lead, renders the value
as 89.5% and changes as 10.5/19.5 percentage points, separates current-data
interpretation from four conditional scenarios, provides named factor/watch
items, and keeps evidence synthesis null. It explicitly states that the stored
data does not establish whether the parliament was dissolved or the background
of the movement.

| Dimension | v4 actual | v5 actual |
|---|---|---|
| Authored structure | 2 prose fields | 6 structured fields |
| Current value/change | Deterministic metric paragraph | Lead + dedicated interpretation |
| Conditional scenarios | None | 4 typed conditional items |
| Follow-up checks | One broad paragraph | Named factors and observable updates |
| Verified evidence | None | None; explicit visible no-source state |
| Exact source links | None | Supported by contract/UI; no real link because verified rows are zero |
| Safety boundary | Deterministic | Deterministic + read-time reconstruction |

## Final development result

- Successful v5 rows: 20 total after display-quality regeneration, across 13
  distinct issues. The latest valid row is retained for four regeneration
  attempts that failed validation.
- Initial TASK-080 attempts: 30; 14 successes, 15 filtered, 1 isolated skip.
- Display-quality regeneration: 10 attempts; 6 successes, 4 filtered.
- Total observed v5 writer cost: USD 0.376609.
- Directly audited context + v5 spend: USD 3.46825105.
- Verified candidates/source links in development: 0/0.
- Latest-row API reconstruction: the 13 representative issues remain valid;
  failed later attempts never replaced them.

## What the user should judge

The v5 structure is substantially clearer and more useful than v4, and the
display-value refinement removed raw 0-to-1 decimals and internal confidence
enums from the reviewed example. Remaining limits are visible:

1. With zero verified sources, scenarios and checklists can use only the market
   definition and stored metrics, so depth is necessarily limited.
2. Some scenario/check wording still focuses on how to verify the market
   condition rather than providing external issue context.
3. The current source-retrieval gate is intentionally strict; improving real
   evidence coverage requires better source inputs, not weaker publication
   thresholds.
4. The production bundle-size warning remains non-blocking and unrelated to
   report correctness.

The local browser is left on the actual development v5 report for the comparison
case. The source-card interaction was separately verified with clearly labeled
localhost fixtures and is not represented as real development evidence.

