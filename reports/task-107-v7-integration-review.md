# TASK-107: V7 integration review

Date: 2026-07-11  
Owner: Reviewer  
Branch: `review/TASK-107-v7-integration-review`  
Status: Complete

## Review result

The v7 request, cache, evidence, wording, and failure path satisfies the
TASK-099 acceptance criteria. No deployment or external-state action was
required.

| Area | Evidence reviewed | Result |
|---|---|---|
| Explicit generation | API appends/joins only; worker owns provider work | Pass |
| Duplicate concurrency | Unique market/fingerprint request, row lock, lease, duplicate join | Pass |
| Retry/recovery | Active lease blocks a second claim; expired lease and failed same-fingerprint request advance attempts | Pass |
| Cache | Metric, definition, context evidence, prompt, policy, and input schema revisions are fingerprinted | Pass |
| Last-good | Stale, generating refresh, provider/validation failure, and malformed latest row retain only a previous valid v7 report | Pass |
| Evidence | Read reconstruction checks exact metric, definition, context, source, supported claim, parent ref, timestamps, and fingerprint | Pass |
| Source policy | A-C may be public with exact level/claim/link; D remains internal | Pass |
| Wording | Positive-first writer plus active English/Korean blocked-language and URL gates | Pass |
| UI failure isolation | Core detail remains visible; request polling stops after repeated endpoint failures; last-good content remains visible | Pass |

## Review fixes

- Replaced lexical UTC timestamp comparisons in the Frontend parser with
  epoch comparisons so equivalent `Z`, `+00:00`, and fractional-second forms
  remain valid.
- Bounded request-status polling after three consecutive failures and surfaced
  a safe retry message without discarding last-good content.
- Added a regression proving a failed request is requeued under the same
  fingerprint/request identity, increments the attempt, succeeds once, and
  creates exactly one report.

## Verification

- V7 focused Backend review: 38 tests passed.
- Full Backend: 438 tests passed; Ruff passed.
- Frontend: typecheck, ESLint, v7 parser regression, and production build
  passed. Only the existing Vite bundle-size warning remains.
- Prohibited-wording scan, Prettier, and `git diff --check` passed.
- No provider call, database write, migration application, dependency,
  infrastructure change, deployment, production action, or legacy deletion
  occurred.
