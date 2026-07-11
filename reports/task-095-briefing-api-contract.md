# TASK-095 — Strict v6 Briefing API Contract

Date: 2026-07-11  
Owner: Backend Implementer  
Branch: `backend/TASK-095-briefing-api-contract`  
Status: complete

## Outcome

- `GET /api/issues/{id}/report` now serves only reconstructed
  `prompt_version="v6"` rows.
- Added the exact `report_mode`, deterministic `observed_change`, strict
  mode-discriminated `briefing`, `resolution_reference`, evidence references,
  exact verified source cards, relationship boundary, limitations, and caution
  response.
- Reloads the linked metric, latest prior snapshot, 24-hour/7-day reference
  snapshots, recent history, exact stored resolution-rule hash/content, and the
  same-episode verified candidates before serving.
- Rejects missing/expired/non-public candidates, invalid sources, URL/domain
  mismatches, wrong timing, unknown/extra fields, basis mismatch, duplicate
  bodies, rule/metric tampering, evidence mismatch, and deterministic-copy
  mismatch.
- If the newest successful v6 row fails reconstruction, the reader tries only
  earlier valid v6 rows. V1–v5 remain audit-only and cannot satisfy fallback.
- Static fallback never invents a report.
- Updated OpenAPI and `backend/API_CONTRACT.md` for the strict v6 contract.

## Verification

- All four mode combinations reconstruct through the public endpoint.
- Exact candidate/source metadata is exposed; internal citation/hash fields are
  withheld.
- No-candidate modes contain no verified-background field or source cards.
- Latest-invalid/previous-v6 fallback passes.
- V5 exclusion, extra field, invalid basis, duplicate body, resolution-rule DB
  mismatch, expired candidate, missing candidate/ref, metric mismatch,
  source-field, URL/domain, episode, and timing attacks fail closed.
- API/OpenAPI focused tests: 63 passed.
- Context-to-v6 integration plus API tests: 64 passed.
- Full Backend suite: 383 passed.
- Ruff and diff checks: passed.

No schema, dependency, provider call, non-test database write, workflow,
infrastructure, deployment, or production action occurred.
