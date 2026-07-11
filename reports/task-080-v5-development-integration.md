# TASK-080 — Development v5 regeneration and integration QA

_Date: 2026-07-11 · Status: Complete_

## Development generation

Three guarded writer batches attempted 30 report generations. The first batch
was entirely rejected before storage and revealed one nullable-window bug. After
the fix and prompt tightening, the next batches stored 14 successful rows across
13 distinct issues.

| Result | Count |
|---|---:|
| Writer attempts | 30 |
| Successful stored v5 rows | 14 |
| Distinct issues with valid v5 | 13 |
| Filtered before storage | 15 |
| Isolated runtime skip before fix | 1 |
| Stored failed v5 rows | 0 |
| Verified candidates / public source links | 0 / 0 |
| Observed v5 writer cost | USD 0.268466 |

All 13 latest per-issue rows independently reconstructed through the public API
path with zero metric, wording, deterministic-copy, evidence-reference, or
source mismatch. Every stored content object has the exact nine public fields
(six authored plus three deterministic fields), three or four scenarios, and
`evidence_synthesis=null` because no candidate passed verification.

The development context ledger records USD 3.09164205. Adding observed TASK-080
v5 writer cost yields USD 3.36010805 in directly audited program spend. Earlier
conservative diagnostics plus the three unintended legacy-writer calls remain
below the previously documented USD 80 conservative ceiling and therefore below
the approved USD 100 cap.

## Browser and contract QA

- Actual development v5: representative issue loaded with three scenarios,
  explicit no-source state, report/data/episode timing, caution, no overflow,
  and zero clean-tab console errors.
- Responsive: 320px, 375px, and 1280px passed on fixture and actual development
  content.
- Evidence states: zero, one, and three candidates passed with exact stored URL,
  domain, source-type label, `_blank`, and `noopener noreferrer` checks. The
  one/three-candidate cases are clearly local fixtures because development has
  no verified candidate.
- Loading, not-yet-generated, and request-failure report states passed without
  hiding the issue timing/caution surface.
- Backend: 333 tests and Ruff pass.
- Frontend: typecheck, ESLint, v5 parser, and production build pass; only the
  pre-existing bundle-size warning remains.

## Limitation

No verified article or official document exists in the current development
data. This is an honest zero-evidence result, not a missing UI implementation.
TASK-081 must show the real no-source page and may use the explicit localhost
fixture only to demonstrate how exact links render if verified evidence later
exists.

