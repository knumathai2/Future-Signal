# TASK-097 — v6 development regeneration and evaluation

Date: 2026-07-11  
Branch: `data-ai/TASK-097-v6-development-regeneration`  
Status: reopened; one clean actual Trump row pending

## Guarded scope

- Environment assertion: `local`.
- Database: configured development database only; no production write.
- Target set: ten actual issues, including the Trump resignation issue.
- The user asked to run only a subset. The initial ten-issue evaluation was
  followed by one explicitly approved two-issue retry; no other market or
  follow-up retry was attempted.
- Internal execution ceiling: USD 8.50, below the approved USD 100 program cap.
- DB-recorded context spend before the run: USD 3.26117420.
- Observed initial writer cost: USD 0.05137300.
- Observed approved two-issue retry cost: USD 0.00731600.
- Total observed TASK-097 writer cost: USD 0.05868900.
- Earlier conservative total was below USD 80; this run therefore remains below
  the approved ceiling even under that conservative accounting method.

## Actual outcomes

| Result | Count |
|---|---:|
| success | 0 |
| malformed strict mode/schema | 3 |
| generic-summary filter | 6 |
| scenario/material mapping filter | 1 |

The approved retry then produced two successful append-only v6 rows:

| Actual issue | Mode | Result | Cost |
|---|---|---|---:|
| Trump resignation | `stable_without_evidence` | success | USD 0.003855 |
| Israeli parliament dissolution | `change_without_evidence` | success | USD 0.003461 |

The deterministic input distribution was nine `stable_without_evidence` cases
and one `change_without_evidence` case. The development candidate ledger still
has no verified public candidates, so the two evidence-present modes did not
occur naturally and were not manufactured. Their UI coverage remains fixture-
only as required by the goal boundary.

Three malformed attempts appended `status=failed` v6 audit rows. Filtered
responses were not stored, matching the existing fail-closed batch behavior.
Before the retry, the public API correctly returned `not_yet_generated` instead
of falling back to the existing v5 Trump report. After the retry, both actual
issues are served as strict v6 responses linked to metric IDs 486 and 495.

## Failure analysis and local correction

The run exposed two prompt-contract reliability gaps without weakening any
safety or evidence gate:

1. The issue-specificity gate compares exact normalized source tokens. When an
   English market title was translated entirely into Korean, otherwise specific
   prose could be rejected as generic.
2. The strict one-based scenario/material mapping was enforced in code but was
   not explicit enough in the writer instructions.

The v6 prompt now supplies bounded `required_issue_anchors` and requires at
least one exact anchor in the issue explanation or first scenario. It also
states the conditional-token rule and exact one-to-one material index mapping.
Local regressions prove an English `Trump` anchor can appear in Korean prose,
generic translated prose without an anchor remains rejected, and every strict
gate remains unchanged. The approved provider retry validated the corrected
shape and mapping constraints. Review of the successful prose found that the
anchor list also retained generic English month/action terms, so the prompt now
prefers proper-name anchors (`Trump`, `Israeli`) and excludes month/category
terms. No extra provider call was made for that non-safety wording refinement;
the successful append-only rows remain unchanged and this limitation is
reported rather than hidden.

## Trump regression

- Actual deterministic mode: `stable_without_evidence`.
- Actual public response: strict successful v6 `stable_without_evidence`.
- Existing v5 row was not used as fallback before or after regeneration.
- Stored payload validation, generation safety validation, and HTTP response
  reconstruction all pass against metric 486 with zero candidate evidence.
- Authored bodies contain no digits, exact/semantic duplicates, unsupported
  current facts, or resolution-rule repetition. The exact rule appears only in
  the default-collapsed reference.
- The actual Browser screen displays an issue-explanation layout rather than a
  rule-repeat layout; the general-scenario notice appears exactly once.

## Verification

- Focused v6 and batch tests: 61 passed before the prompt correction.
- Focused post-retry v6/batch tests: 64 passed; Ruff and diff clean.
- Full Backend suite before Reviewer closeout: 387 passed; Reviewer reruns and
  records the final total after the proper-name anchor regression is added.
- Frontend typecheck, lint, strict parser regression, and production build pass.
- Browser QA found and removed one duplicate general-scenario notice, then
  passed all four fixtures at 320/375/768/1024/1280px with exact notice counts,
  collapsed rule references, no overflow, and no console errors in clean tabs.
- No dependency, schema, migration, workflow, infrastructure, deployment, or
  production action occurred.

## Completion-gate audit

| TASK-097 requirement | Evidence | Status |
|---|---|---|
| Development-only scope and append-only behavior | `ENV=local` assertion; three new failed v6 audit rows; no production action | Pass |
| Cost boundary | USD 0.058689 total observed TASK-097 cost; conservative program total remains below USD 100 | Pass |
| At least ten actual issues | Exactly ten actual markets evaluated, including Trump resignation | Pass |
| Natural mode accounting | Nine stable/no-evidence and one change/no-evidence; evidence modes absent because verified candidates are zero | Pass |
| Missing natural modes handled without manipulation | Evidence-present modes retained as development-only fixtures | Pass |
| Success/rejection/cost/evidence/duplicate record | Two successes, ten initial rejection outcomes, exact cost and zero verified evidence recorded; no duplicate rejection occurred | Pass |
| Successful actual v6 report | Two strict successful rows reconstruct through the HTTP API | Pass |
| Trump authored-body rule-repeat regression | Actual stored/HTTP/UI result has no rule repetition and keeps the exact rule collapsed | Pass |

Post-review audit found that the successful Trump prose repeated the English
month `december` in two authored sections and that both successful rows retained
generic English action terms. New generation/read-time gates reject authored
month/deadline words and every English token except supplied proper-name
anchors. The current HTTP API therefore fail-closes both append-only rows as
`not_yet_generated`; the rows are preserved for audit.

TASK-097 is reopened. One additional clean Trump regeneration is required to
prove the corrected date/language gates and restore a genuine actual review
screen. This is a new provider call beyond the two-issue approval and is not
authorized yet. TASK-098 returns to assigned status.
