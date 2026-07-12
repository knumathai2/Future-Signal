# Historical AI report contracts: v1-v7

_Status: archive index updated for the active v8 runtime on 2026-07-12._

This file summarizes superseded report contracts. It is not an active prompt,
API contract, or wording policy. Current behavior is documented in
`backend/API_CONTRACT.md`, current design documents, and executable schemas.
Accepted decisions remain unchanged in `memory/decisions.md`; detailed removed
artifacts remain recoverable from Git history.

## Version map

| Version | Active period | Governing record | Historical shape | Superseded by |
|---|---|---|---|---|
| v1 | 2026-07-09 to 2026-07-10 | ADR-003, ADR-008, TASK-015 | Initial fixed template and stored success/empty read state | ADR-028 / v2 |
| v2 | 2026-07-10 | ADR-028, ADR-030, TASK-043 | Fixed issue explainer with conditional sections, checks, limitations, and caution | ADR-033 / v3 |
| v3 | 2026-07-10 to 2026-07-11 | ADR-033, ADR-034, TASK-049~053 | Eight-field evidence-first template with three authored prose fields | ADR-038 / v4 |
| v4 | 2026-07-11 | ADR-038, ADR-043~047, TASK-056~065 | Seven-field change episode linked to one metric and verified context candidates | ADR-048 / v5 |
| v5 | 2026-07-11 | ADR-048, ADR-049, TASK-075~091 | Evidence-bounded narrative, scenarios/checks, resolution rules, exact sources, and explicit zero-source state | ADR-050 / v6 |
| v6 | 2026-07-11 | ADR-050, TASK-092~098 | Four deterministic modes based on observed change and accepted context | ADR-051 / v7 |
| v7 | 2026-07-11 | ADR-051, TASK-099~111 | Fingerprinted on-demand request/lease/cache flow with flexible evidence-linked sections and A-C sources | TASK-112 / v8 |

Dates identify repository contract activation, not deployment.

## Current v8 transition

V8 keeps the durable evidence, source-parent, request, lease, cache,
last-known-good, timing, limitation, caution, and publication blockers from v7.
It changes the authored structure to an issue-centered headline, summary, and
two-to-six typed sections. TASK-113~117 add wider bounded source discovery,
safe retry, contextual wording validation, and individually validated NDJSON
blocks delivered through SSE.

The active API reconstructs successful v8 rows only. Under explicit approval,
the configured local development database removed stored v1-v7 reports and v7
request/event history. V8 reports, requests, events, blocks, metrics,
snapshots, context, and definition evidence remain. No production database was
modified.

## Permanent invariants

These rules are not archived away:

- aggregate public data only;
- no unsupported future-result or relationship assertion;
- honest data-as-of timing and interpretation caution on every data surface;
- exact reconstruction of source URLs, titles, claims, metrics, dates,
  entities, evidence references, and fingerprints;
- unsafe links or mismatched evidence block publication;
- provider or validation failure preserves the previous valid result;
- current prohibited-language and source-attribution policy remains active;
- deployment, production writes, dependencies, schema, public API,
  infrastructure, and wording-policy changes retain their approval gates.

## Authoritative history

| Concern | Source |
|---|---|
| Accepted decisions and approval boundaries | `memory/decisions.md` |
| Completed implementation ledger | `tasks/completed.md` |
| Active v8 public contract | `backend/API_CONTRACT.md` and `app/schemas/issues.py` |
| Writer and reconstruction implementation | `backend/app/core/ai_report.py`, `backend/app/core/on_demand_briefing.py`, `backend/app/api/routes/issues.py` |
| Current policy | `AGENTS.md`, `standards.md`, `memory/glossary.md`, Service Design, Technical Design, UX Design |
| Retained cost/evidence/failure reports | `reports/` entries selected by `docs/document-retention-manifest.md` |
| Removed detailed artifacts | Git history before TASK-122 |

## Runtime compatibility

Historical writer, schema, fixture, and batch compatibility code may still
exist for tests or reconstruction support. Its presence does not make a
historical public contract active. Removing that code remains a separately
scoped TASK-109 action; migrations and accepted audit records are permanent.
