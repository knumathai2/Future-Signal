# ISS-027 — Scenario first-response failure

_Date: 2026-07-13_

## Reproduction

1. Open the scenario tab for the U.S.–Russia nuclear-agreement issue.
2. Create a scenario session and submit its first message.
3. Observe that the request reaches a terminal failed state and the Frontend
   displays the generic response-unavailable message.

## Root cause

The request was queued and claimed normally, and the provider returned a
schema-valid response. The response omitted the exact current user-turn ref
from `premise_refs`, so the deterministic validator recorded
`current_turn_ref_missing` before storing any assistant content or blocks.
Eight recent requests across two issues showed the same rule, making this a
repeated output-contract compliance problem rather than a Frontend, SSE,
worker-launch, or individual-input failure.

## Impact

- No unsafe or unreferenced assistant response was published.
- The affected user turn consumed one session turn but had no visible assistant
  response.
- Starting another session was likely to repeat the same failure while the
  prompt contract remained ambiguous.

## Fix

`scenario-writer-3` now:

- supplies the current message as a typed `current_user_turn` object;
- repeats its exact ref in `reference_contract.required_premise_ref`;
- places that literal ref in the minimum `required_output.premise_refs` array;
- lists optional refs separately in deterministic order; and
- keeps the existing fail-closed ref validation without automatic correction
  or retry.

## Verification and prevention

- Added a regression for the exact serialized ref contract.
- Ruff and all 549 Backend tests pass.
- One purpose-bound local evaluation made one provider call, cost USD
  0.0063915, and stored one assistant turn plus three validated blocks.
- Future prompt versions should place mandatory dynamic values inside the
  concrete output example, not only in descriptive prose.

No API, schema, dependency, secret, infrastructure, deployment, production, or
wording-policy state changed.
