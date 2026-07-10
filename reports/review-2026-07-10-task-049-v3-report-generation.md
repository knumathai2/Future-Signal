<!--
Purpose:        PR #49 review findings for TASK-049 v3 report generation
Owner:          Reviewer
Update Trigger: PR #49 review follow-up or resolution
Harness Version: 1.1
-->

# PR #49 Review - TASK-049 v3 Report Generation

## Verdict

**Request Changes**

- Repository: `knumathai2/Future-Signal`
- Pull request: `#49`
- Reviewed head: `ae76a6b147c9f45e16dd56f65b1d43e22f218ff2`
- GitHub review:
  <https://github.com/knumathai2/Future-Signal/pull/49#pullrequestreview-4668601361>

## Findings

### P1 - `possible_drivers` omits the candidate title and date

ADR-033 defines this field as a deterministic index of the PM/Data-reviewed
candidate title and recorded date. The implementation loads both values but
returns one generic candidate-present literal, so different candidates produce
the same output and the TASK-049 completion criterion is not met.

### P1 - Structured metric values are not checked against generated prose

`current_data_reading` is copied from the model response, while semantic
validation checks only the caution literal, candidate literal, and external
context qualifier. A reproduction with `current_value=0.63` and generated text
claiming 99% passed both safety and semantic checks. This permits unsupported
metric values to be stored.

### P1 - Korean safety pattern rejects the approved negative disclaimer

The global `원인` pattern rejects ADR-033's approved negative relationship
wording (`변화의 원인으로 제시되지 않습니다`). The approved contract example
therefore fails before storage even though it explicitly avoids a causal
claim.

### P2 - External-context qualifier rejects the approved Korean example

The semantic helper requires the literal `candidate` or `후보` in addition to
a negative relationship phrase. ADR-033's approved example says `수동 검토를
마친 맥락 메모` and contains no literal `후보`, so it fails this check even if
the global pattern is corrected.

## Verification Evidence

- Full backend suite at PR head: `175 passed in 0.72s`
- Ruff at PR head: `All checks passed!`
- Focused reproductions confirmed:
  - reviewed candidate title/date absent from `possible_drivers`;
  - mismatched 99% generated reading accepted for a 63% structured input;
  - approved Korean negative disclaimer rejected by the phrase filter and the
    external-context semantic check.

## Required Follow-up

- Include reviewed candidate title/date in deterministic
  `possible_drivers` output.
- Make metric-bearing report prose deterministic or validate all metric/window
  claims against structured inputs before storage.
- Narrow the Korean causal filter so approved negative relationship wording is
  accepted.
- Align the external-context qualifier with ADR-033's approved Korean example.
- Add regression tests for each corrected behavior and re-run the complete
  backend suite and Ruff.

## Follow-up Resolution

The requested changes were implemented in PR head commit `363bf2f`:

- `possible_drivers` now includes the reviewed candidate title and date.
- Metric-bearing `current_data_reading` prose is checked against structured
  current and change values before storage.
- The approved Korean negative relationship disclaimer is accepted while
  positive causal wording remains blocked.
- The approved `맥락 메모` external-context qualifier is accepted.

The four review threads were answered and resolved. The fixed head passes 179
backend tests and Ruff, and the follow-up GitHub review is `APPROVED`.
