# TASK-018: Copy/Wording Lint Pass

Date: 2026-07-09
Owner: PM / Planner
Branch: `pm/TASK-018-copy-lint`
Verdict: **Pass with notes**

## Scope Checked

- Frontend user-facing strings in `frontend/src` and `frontend/index.html`
- Static/fallback issue data in `frontend/src/data/dummyIssues.ts`
- Backend fallback/API/report strings in `backend/app`, `backend/API_CONTRACT.md`,
  and `backend/README.md`
- AI report prompt templates, batch report helpers, and safety filter in
  `backend/app/core/ai_report.py` and `backend/app/core/ai_report_batch.py`
- Related-event candidate seed data in `backend/app/db/seed_related_events.py`
- Relevant tests with surfaced/sample text:
  `backend/tests/test_ai_report.py`,
  `backend/tests/test_seed_related_events.py`,
  `backend/tests/test_issues_contract.py`, and
  `backend/tests/test_issues_live.py`
- Day 4 demo/report docs:
  `reports/task-040-demo-script-deck-draft.md`,
  `reports/task-040-demo-script-deck-draft-prompt.md`,
  `reports/task-041-report-generation-readiness.md`,
  `reports/task-043-issue-explainer-report.md`, and
  `reports/task-044-korean-issue-titles.md`

## Policy References

- `AGENTS.md` absolute product-safety restrictions
- `standards.md` Content Safety Lint
- `memory/glossary.md` wording policy and domain terms
- `docs/ux-design/02-copy-safety-disclaimers.md` Sections 4-8
- Related-event rule: candidate/context, not cause
- Data-bearing screen rule: nearby data-as-of timing plus interpretation-caution
  context

No wording policy, disclaimer policy, public API shape, schema, dependency,
infrastructure, deployment, external AI call, or database write was changed.

## Commands Run

```bash
git status --short --branch
git branch --list pm/TASK-018-copy-lint
git switch -c pm/TASK-018-copy-lint
```

Ran the three requested `rg` scans over the requested path set:

- hard-block prohibited wording scan
- use-carefully wording scan
- causal/future-prediction/Korean-equivalent scan

Validation:

```bash
cd frontend
npm run typecheck
npm run lint
npm run build

cd ../backend
.venv/bin/ruff check app tests
DATABASE_URL= .venv/bin/pytest tests/test_ai_report.py tests/test_seed_related_events.py tests/test_issues_contract.py tests/test_issues_live.py
```

Final validation results:

- Frontend typecheck: passed
- Frontend lint: passed
- Frontend build: passed with the known Vite/Recharts chunk-size warning
- Backend ruff: passed
- Targeted backend tests: passed, 68 tests

## Findings

| ID | Surface | Finding | Action | Status |
|---|---|---|---|---|
| F-001 | AI report prompt template | Model-facing prompt used a hard-block word in neutral descriptive text and used `Confidence level` as a prompt label. | Changed to `concise`, `limited history`, and `Data reliability/caution level`. Internal field name remains unchanged. | Resolved |
| F-002 | Dashboard weekly rows | Secondary dashboard rows showed a change value and caution badge without their own nearby data-as-of timestamp. | Added compact `데이터 기준 시각` text to each weekly row. | Resolved |
| F-003 | TASK-044 report doc | Internal report copy still used one hard-block word in descriptive task prose. | Changed to `compact issue display title` and removed the raw-word note. | Resolved |
| F-004 | Safety filters and rejection tests | Raw scans find prohibited words in banned-word lists and intentionally unsafe test fixtures. | Classified as allowed policy/test references; tests prove rejection behavior. | Allowed |
| F-005 | Day 4 demo/deck docs | Demo script and Q&A keep issue-monitoring framing and include caution/candidate wording. | No code/doc change needed beyond F-003. | Pass |

## False Positives / Allowed References

- `backend/app/core/ai_report.py` keeps prohibited terms in the explicit
  never-use list and runtime safety filter.
- `backend/tests/test_ai_report.py`,
  `backend/tests/test_ai_report_batch.py`, and
  `backend/tests/test_seed_related_events.py` intentionally include unsafe
  phrases to assert rejection.
- `backend/tests/test_issues_contract.py` intentionally asserts public paths do
  not expose banned terminal vocabulary.
- Remaining `signal` hits are internal API/schema/batch names or the accepted
  `expectation_shift` system term. Frontend visible marker labels render as
  neutral Korean observation wording.
- Remaining causal/Korean hits in UI and demo docs are caution language such as
  `원인으로 제시하지 않습니다`, which is the required "not cause" framing.

## Hard-Block Findings

No unresolved hard-block shipped wording remains in the checked surfaces.

Resolved hard-block-adjacent items:

- AI report prompt wording now avoids direct hard-block vocabulary outside the
  explicit never-use/filter lists.
- TASK-044 report prose no longer uses the raw hard-block term found by the
  scan.

## Use-Carefully Wording Review

- `signal`: no standalone urgency-styled user-facing copy found. Internal
  route/schema/batch names remain unchanged because they are established
  technical contract terms. UI-facing marker text says `관측 변화` and `5pp
  기준선`.
- `confidence`: frontend does not render raw `confidence_level`; it renders
  caution badge labels. The AI prompt label was changed to
  `Data reliability/caution level`.
- `watch`, `alert`, `momentum`, `market activity`, and `probability spike`: no
  unsafe user-facing use found in the checked surfaces.

## Data-As-Of + Interpretation-Caution Audit

- Dashboard header: data-as-of timestamp present; dashboard caution notice
  present.
- Issue cards: each card has a caution badge and data-as-of timestamp.
- Dashboard weekly rows: caution badge already present; data-as-of timestamp
  added in this task.
- Detail header and metric area: caution badge, data-as-of timestamp, and
  brief caution notice present.
- Chart area: caution badge, data-as-of timestamp, and "not cause" context
  present; insufficient-history state keeps timing.
- Report card: caution badge, report/fallback data-as-of timestamp, generated
  timestamp when present, and summary caution notice present.
- Backend issue list/detail/history/report responses expose `data_as_of` where
  data is returned and preserve neutral empty states where report/history data
  is absent.

## Related-Event Candidate Audit

- Static dummy related-event notes use Korean manual-candidate/not-cause
  wording.
- `backend/app/db/seed_related_events.py` uses a shared suffix:
  candidate context entered manually, not presented as a cause.
- Tests assert every related-event note includes the suffix, avoids causal
  connectors, and avoids prohibited vocabulary.
- No automated news-to-market matching or participant-level browsing was
  introduced.

## Remaining Day 5 Risks

- Final slide screenshots and captions should be rechecked after capture,
  especially if live issue titles appear in images.
- Known non-blocking frontend build warning remains: Vite reports a large
  bundled chunk, likely from Recharts.
- Static backend fallback sample titles remain English; if that path is used in
  the presentation, use the existing fallback narration and visible data-as-of
  framing.

## Verdict

**Pass with notes.** All blocking findings found during TASK-018 were resolved,
and the remaining notes are Day 5 presentation hygiene rather than Day 4
closeout blockers.
