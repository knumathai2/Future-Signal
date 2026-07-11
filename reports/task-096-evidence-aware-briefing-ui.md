# TASK-096 — Evidence-aware briefing UI

Date: 2026-07-11  
Branch: `frontend/TASK-096-evidence-aware-briefing-ui`

## Outcome

The issue detail now accepts only the strict v6 report contract and renders one
of four evidence-aware layouts. Deterministic observed values remain outside
model-authored prose, verified material appears only when exact stored source
records exist, and the resolution rule is available only through the collapsed
`판정 기준 보기` disclosure.

## Implemented behavior

- `change_with_evidence`: observed change, verified background and exact source,
  then conditional interpretations.
- `change_without_evidence`: observed change, compact no-evidence notice,
  general-scenario notice, conditional scenarios, and material checks.
- `stable_with_evidence`: issue explanation, verified background and exact
  source, then general conditional scenarios.
- `stable_without_evidence`: general issue explanation, conditional scenarios,
  and scenario-linked material checks without an empty verified section.
- The parser rejects legacy versions, extra fields, invalid mode/evidence
  combinations, unsafe source links, metric inconsistencies, rule leakage,
  unsupported numeric prose, and exact or normalized semantic duplication.
- External evidence links use the exact stored URL with `target="_blank"` and
  `rel="noopener noreferrer"`.
- The disclosure is a native button with `aria-expanded`, `aria-controls`, a
  hidden controlled panel, a 44px minimum target, and visible keyboard focus.
- The data-as-of, relationship boundary, limitations, and interpretation
  caution remain visible.

## Verification

- `npm run typecheck`: passed.
- `npm run test:report-parser`: passed for all four modes plus adversarial cases.
- `npm run lint`: passed.
- `npm run build`: passed; only the existing bundle-size advisory remains.
- Browser QA covered all four modes at 320, 375, 768, 1024, and 1280px. All 20
  combinations had the expected mode, a collapsed rule reference, no horizontal
  overflow, and the correct evidence/general-notice section visibility.
- A visual Trump regression exposed a duplicate general-scenario notice in the
  stable/no-evidence layout. The notice now has one owner inside the general
  issue-explanation card; a second 20-combination Browser pass verified exact
  notice counts (zero for change/evidence, one for every general-scenario mode).
- A development-only Trump fixture uses the exact development metric values and
  issue-specific general explanation so the intended post-change layout can be
  reviewed without presenting it as a successful stored provider result.
- Fixture-mode console errors were limited to the expected API failures caused
  by intentionally running the Frontend without the Backend; the final real-data
  flow is rechecked in TASK-098.
- Changed user-facing strings passed the project wording scan.

## Scope

No dependency, schema, provider, database, workflow, infrastructure,
deployment, or production change occurred.
