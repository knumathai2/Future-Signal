# ISS-028 — Scenario output-contract stabilization

_Date: 2026-07-13_

## Reproduction

1. Restart the local Backend with the ISS-027 current-ref fix loaded.
2. Submit a new first scenario message.
3. Observe a terminal `assumption_promotion` failure even though the required
   current-turn ref is present.

## Root cause

ISS-027 fixed the first missing-ref failure, but the output contract still gave
the provider two choices that could fail independently:

- conditionally frame the current user message in natural Korean prose; and
- select and copy any optional evidence identifiers it used.

The real follow-up request omitted an accepted assumption-framing marker. A v4
prompt made an exact safe prefix mandatory, but its one evaluation appended an
unknown optional ref and failed closed at the next structural gate.

## Fix

`scenario-writer-5` removes both choices from the provider:

- `answer_contract.required_prefix` contains the exact safe prefix that must
  begin `answer_markdown`;
- `reference_contract.required_premise_refs` contains the complete ordered ref
  array for the current turn and stored market definition;
- additional, missing, reordered, and unknown refs fail validation; and
- the server does not correct the provider response or retry a failed request.

## Verification

- Ruff passes.
- All 550 Backend tests pass.
- The one v4 evaluation failed closed with `unknown_premise_ref`, cost USD
  0.006011, and stored no assistant content.
- One new v5 evaluation made one provider call, cost USD 0.0072395, and stored
  one assistant turn plus three validated blocks.
- The local reload child started after the v5 source change, and health reads
  succeed through both `127.0.0.1:8000` and the Vite proxy.

The historical failed browser turn remains failed by design. A new message or
new session uses v5. No public API, schema, dependency, secret, infrastructure,
deployment, production, or wording-policy state changed.
