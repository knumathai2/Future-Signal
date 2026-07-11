# TASK-116 — Contextual wording safety policy

Date: 2026-07-11  
Owner: PM + Data/AI + Backend  
Branch: `pm/TASK-116-contextual-wording-policy`

## Approval and outcome

The user explicitly approved changing the flat prohibited-expression policy.
Active v8 now evaluates semantic role and exact section evidence instead of
rejecting every occurrence of six Korean expressions. Safety gates were not
replaced by model judgment; the classifier is deterministic and fail-closed.

## Rule matrix

| Class | Result |
|---|---|
| Transactional, financial-return, participant-following, endorsement, English hard blocks | Always reject |
| `확정`, `보장`, `추천`, `기회`, `전망`, `원인` in explicit negation/limitation | Allow |
| The same terms in a verification inquiry such as `확정 여부` | Allow |
| Positive use with exact same-section source ref, same-strength supported-claim marker, and visible attribution | Allow |
| Source ref without attribution, attribution without semantic support, bare assertion, ambiguity, future outcome, or unsupported cause | Reject |

Headline and summary have no section evidence scope, so they may use only the
source-free safe forms. V1-v7 retain historical flat filters.

## Implementation

- Added sentence-level active-v8 contextual classification.
- Added Korean/English support-marker maps for the six contextual expressions.
- Required visible attribution in the same authored sentence.
- Ran the identical validator before storage and during reconstruction.
- Advanced the active policy to `v8-contextual-wording-1`.
- Allowed reconstruction with the historical `v8-issue-centered-1`
  fingerprint so previous valid reports remain last-known-good and become
  stale relative to the new policy.

## Verification

- 18 focused v8 wording tests passed.
- 25 combined v8/on-demand tests passed before the full run.
- Full Backend: 482 tests passed.
- Ruff: full Backend clean.
- Live read: the prior real v8 report reconstructed successfully as `stale`.
- No provider call, database write, schema, migration, public API, dependency,
  infrastructure, deployment, or production action occurred.

Adversarial coverage includes unsupported certainty, negative certainty,
verification inquiry, source-supported certainty, attribution with insufficient
source strength, institutional recommendation, procedural opportunity,
guarantee, attributed outlook, attributed cause, and future-outcome assertion.
