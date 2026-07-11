# TASK-098 — Evidence-aware briefing integration review

Date: 2026-07-11  
Branch: `review/TASK-098-evidence-aware-briefing-integration`  
Status: reopened; final actual-row proof pending

## Review outcome

The v6 briefing flow passes the approved four-mode contract from deterministic
selection through strict storage, read-time reconstruction, Frontend parsing,
mode-specific rendering, and the collapsed resolution reference. Two genuine
development rows prove the stable/no-evidence and change/no-evidence paths. The
evidence-present paths remain fixture/integration-test only because the honest
development state contains zero verified context candidates.

**Reopening note:** the final visual audit found `december` repeated in two
Trump authored sections and generic English action terms in both live rows.
This contradicted the no-date-repeat and complete-Korean requirements even
though the earlier digit/rule checks passed. New read-time gates now reject both
rows, so the actual-row claims below describe the pre-gate evidence and no
longer satisfy final completion. TASK-098 is reopened until one clean actual
Trump row passes the new gates.

## Requirement audit

| Requirement | Evidence | Result |
|---|---|---|
| Deterministic four-mode selection | Parametrized Backend tests cover all change/evidence combinations and insufficient data; the model never selects the mode | Pass |
| Exact observed change ownership | Metric ID/current/change/threshold are deterministic; authored body digit checks pass; actual Trump page shows the current value once in the metric area | Pass |
| Verified/general evidence separation | Discriminated schemas, exact candidate IDs, strict bases, exact source reconstruction, and the required general-scenario notice | Pass |
| No verified material state | Actual Trump and Israeli rows have zero candidates and no empty verified-background region | Pass |
| Evidence-present state | Backend API/integration tests and three exact-source Frontend fixtures validate candidate/source order, URL/domain/time/type, secure links, and same-episode references | Pass |
| Rule reference ownership | Exact stored rule is absent from authored bodies and visible only after the native `판정 기준 보기` disclosure is expanded | Pass |
| Duplicate prevention | Exact and normalized semantic body gates pass; the duplicate general notice found during Browser review was removed and its exact occurrence count is now one | Pass |
| No legacy fallback | Before regeneration the actual Trump endpoint returned `not_yet_generated`; after regeneration it serves only its strict v6 row, never the stored v5 row | Pass |
| Safety boundaries | Stored payload rerun rejects numbers, URLs, unsupported current facts, rule leakage, bad candidates, causality/action wording, and banned wording; changed UI copy scan is clean | Pass |
| Data timing and caution | Actual and fixture cards retain data-as-of, generated-at, episode-at, relationship boundary, limitations, and interpretation caution | Pass |
| Responsive/accessibility | Four modes × 320/375/768/1024/1280px passed with no overflow; actual Trump also passed at 320px. Disclosure is a native button with `aria-expanded`, `aria-controls`, controlled hidden panel, 44px target, and focus-visible styling | Pass |
| Actual Trump regression | Pre-gate row had no digits or exact rule leak but repeated `december`; current read gate returns `not_yet_generated` | **Incomplete** |
| Actual change regression | Pre-gate row retained generic English; current read gate returns `not_yet_generated` | **Incomplete** |

## Actual development evidence

| Issue | v6 row | Metric | Mode | Candidates | Safety/API/UI |
|---|---|---:|---|---:|---|
| Trump resignation | `eda250ef-9ad0-49a4-aff1-09641b1de873` | 486 | `stable_without_evidence` | 0 | Rejected: authored date |
| Israeli parliament dissolution | `8a9f09a5-5f7e-4d84-a666-a912c5b440ba` | 495 | `change_without_evidence` | 0 | Rejected: generic English |

The approved two-issue retry cost USD 0.007316. Total observed TASK-097 writer
cost was USD 0.058689. DB-recorded context spend remained USD 3.26117420, and
the previously recorded conservative program total plus this run remains below
the human-approved USD 100 ceiling.

## Verification commands and Browser evidence

- Backend: 390 tests passed after the new date/language gates; Ruff and
  `git diff --check` clean.
- Frontend: typecheck, ESLint, strict v6 parser regression, production build,
  and diff check passed. The existing bundle-size advisory is unchanged.
- Changed user-facing copy: no prohibited wording, outcome assertion, causal
  assertion, likelihood ranking, or action-direction match.
- Fixture Browser matrix: 20/20 combinations passed with exact notice counts,
  default-collapsed rule reference, correct mode, and no horizontal overflow.
- Pre-gate actual Browser checks passed structurally, but the content audit
  reopened them. Current API behavior is the honest `not_yet_generated` state.

## Remaining limits

1. The development database still has zero verified context candidates, so no
   genuine `change_with_evidence` or `stable_with_evidence` row exists. Those
   modes are proven by strict Backend/API tests and development-only UI fixtures,
   not by manufactured database evidence.
2. The two successful append-only rows were generated before the final
   proper-name-only anchor refinement and retain several generic English words
   (`december`, `resign`, `dissolved`). The rows remain safe and structurally
   valid, but their Korean prose is less polished than desired. Future prompts
   now expose only proper-name anchors such as `Trump` and `Israeli`; no third
   provider call or in-place row edit was performed.
3. Rapid multi-tab local navigation can still saturate the development session
   pool (ISS-013). Serial clean-tab review passed; no infrastructure or runtime
   pool setting was changed.
4. Adding an independent verifier model to scheduled runtime configuration
   remains separately approval-gated. TASK-094 makes missing configuration fail
   visibly but does not mutate workflow/runtime settings.

## Scope confirmation

No dependency, schema, migration edit/application, production database write,
workflow/runtime configuration change, infrastructure mutation, deployment, or
production action occurred during TASK-098.
