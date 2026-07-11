# Historical AI report contracts: v1-v6

Status: historical contract index prepared by TASK-100 on 2026-07-11.

This directory records how the report contract evolved before the proposed v7
on-demand briefing program. It is an archive map, not an active writer prompt.
Stored report rows, migrations, ADRs, and audit records remain authoritative
history. The current runtime remains v6 until a later approved task activates
v7.

## Version map

| Version | Active period | Governing record | Public shape and generation model | Superseded by | Runtime state at TASK-100 |
|---|---|---|---|---|---|
| v1 | 2026-07-09 to 2026-07-10 | ADR-003, ADR-008, TASK-015 | Initial fixed template stored in `ai_reports`; read route returned a successful stored row or the neutral empty state. | ADR-028 / v2 | Audit-only rows; legacy generator compatibility remains in shared code. |
| v2 | 2026-07-10 | ADR-028, ADR-030, TASK-043 | Fixed issue explainer with issue meaning, current reading, conditional developments, checks, limitations, and caution. | ADR-033 / v3 | Audit-only rows and legacy schema compatibility. |
| v3 | 2026-07-10 to 2026-07-11 | ADR-033, ADR-034, TASK-049~053 | Eight-field fixed contract. Three prose fields were model-authored; evidence comparison, context, limitations, and caution were deterministic. Context remained manual-only. | ADR-038 / v4 | Historical MVP contract; generator, tests, and API documentation remain. |
| v4 | 2026-07-11 | ADR-038, ADR-043~047, TASK-056~065 | Seven-field change episode linked to one metric and zero-to-three independently verified context candidates. Only two prose fields were model-authored. | ADR-048 / v5 | Audit-only public rows; research, verification, writer, query, and compatibility code remain. |
| v5 | 2026-07-11 | ADR-048, ADR-049, TASK-075~091 | Evidence-bounded structured narrative with one-to-four scenarios, resolution-rule evidence, reference values, observed history, basis labels, exact-source links, and explicit no-source state. | ADR-050 / v6 | Audit-only public rows; generator, read helpers, schemas, fixtures, and tests remain. |
| v6 | 2026-07-11 onward | ADR-050, TASK-092~098 | Four deterministic modes selected from significant 24-hour change and verified-context presence. Strict evidence bases, single-owner metric/rule display, mode unions, and v6-only fallback. | Proposed ADR-051 / v7, not active | Current runtime contract. Two development rows were later withheld after stricter authored-date and non-anchor-language checks; the endpoint may honestly return the neutral empty state. |

The dates above identify repository contract activation, not deployment dates.
No deployment is implied by this archive.

## Authoritative references

| Concern | Historical source |
|---|---|
| Decisions and supersession | `memory/decisions.md` (ADR-003, ADR-028, ADR-030, ADR-033, ADR-034, ADR-038, ADR-043~050) |
| Public response history | `backend/API_CONTRACT.md` and the corresponding task reports |
| Writer/storage implementations | `backend/app/core/ai_report.py`, `backend/app/core/ai_report_batch.py` |
| Read-time reconstruction | `backend/app/api/routes/issues.py`, `backend/app/db/queries.py`, `backend/app/schemas/issues.py` |
| Frontend contracts | `frontend/src/types/issue.ts`, `frontend/src/utils/reportParser.ts`, `frontend/src/data/reportFixtures.ts` |
| Product/service/UX policy | `docs/prd/`, `docs/service-design/`, `docs/tech-design/`, `docs/ux-design/` |
| v3-v6 task evidence | `reports/task-043-issue-explainer-report.md`, `reports/task-049-*`, `reports/task-055-*`, `reports/task-064-*`, `reports/task-075-*`, `reports/task-082-*`, `reports/task-092-*`, `reports/task-098-*` |

## Cross-version invariants that are not archived away

The following constraints come from the project constitution or current
product policy and remain binding unless separately amended with human
approval:

- aggregate public data only; no individual-participant browsing;
- no assertion of a future result and no invented causal explanation;
- every data-bearing screen keeps an honest data-as-of timestamp and an
  interpretation-caution notice;
- public source URLs, titles, claims, metrics, dates, entities, and evidence
  references must reconstruct from stored inputs;
- unsafe links or mismatched evidence block publication;
- report and context writes are append-only, with prior rows retained for
  audit;
- provider failure keeps the last valid result when one exists and never
  corrupts market-data collection;
- current prohibited product-language and non-inducement rules remain active
  until an explicitly approved policy amendment says otherwise; and
- deployment, production writes, new dependencies, schema changes, public API
  changes, infrastructure changes, and legacy deletion retain their separate
  approval gates.

## Transition and cleanup map

TASK-109 may consider removal only after v7 has passed TASK-107 and TASK-108
and the user has accepted v7. Even then, deletion needs separate approval.

Preserve permanently:

- migration files and database rows;
- ADRs, task reports, cost/evidence audits, and this archive;
- the minimum reader or diagnostic tooling needed to explain stored history;
- source provenance and evidence records referenced by historical reports;
- current safety, timestamp, and aggregate-data controls.

Potential cleanup candidates after acceptance:

- v1-v6 prompt builders and generation dispatch paths no longer called by v7;
- v1-v6 public response schemas and Frontend parsers no longer reachable;
- version-specific fixtures and tests duplicated by v7 coverage;
- scheduled report-generation flags and compatibility branches superseded by
  the approved on-demand service;
- active product-document paragraphs that describe v1-v6 as current behavior.

TASK-100 does not delete, disable, or relabel any runtime implementation.
