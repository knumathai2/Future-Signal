# TASK-093 — Deterministic v6 Briefing Mode Generator

Date: 2026-07-11  
Owner: Data/AI Implementer  
Branch: `data-ai/TASK-093-briefing-mode-generator`  
Status: complete

## Outcome

- Added `V6_PROMPT_VERSION="v6"` without a migration or dependency.
- Deterministically selects `change_with_evidence`,
  `change_without_evidence`, `stable_with_evidence`, or
  `stable_without_evidence` from the existing 24-hour ±5pp signal rule and the
  independently reconstructed verified-candidate list.
- Added four strict discriminated writer-output shapes. Extra, missing, or
  wrong-mode fields fail parsing.
- Removed current value, change amount, dates, and exact resolution-rule prose
  from the writer prompt. Those values are stored once in deterministic
  `observed_change` and `resolution_reference` objects.
- Added explicit `market_definition`, `verified_context`, and
  `general_scenario` authored blocks. Verified prose retains exact candidate
  IDs; source-free scenarios cannot masquerade as verified background.
- Scenario-specific material items reference their scenario index, and every
  general scenario must have at least one matching material item.
- Added Unicode/number/date normalization, exact-body and title-only duplicate
  detection, token-overlap duplicate rejection, resolution-rule overlap
  blocking, unsupported-current-fact checks, candidate-ID checks, and the
  existing prohibited/causal wording filters.
- Added append-only v6 batch generation with budget reservation, failure
  isolation, and v6 prompt-version selection. Existing rows are never updated
  or removed.

## Verification

- Four mode-selection combinations and insufficient-data behavior.
- Strict per-mode parsing, wrong-mode and extra-field rejection.
- Valid generation for all four modes.
- Metric/date omission from prompts and authored prose.
- Resolution-rule repetition, same-body/different-title duplication,
  unsupported recent facts, unknown candidate IDs, and scenario/material
  mismatch rejection.
- SQLite append-only batch storage of the exact v6 envelope.
- Focused tests: 59 passed.
- Full Backend suite: 369 passed.
- Ruff: passed.
- `git diff --check`: passed.

No provider call, non-test database write, workflow change, dependency,
migration, infrastructure change, deployment, or production action occurred.
