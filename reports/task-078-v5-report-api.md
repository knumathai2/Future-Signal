# TASK-078 — v5 report storage and public API

_Date: 2026-07-11 · Status: Complete_

## Result

- Kept append-only `ai_reports.content` JSONB storage; no migration or dependency
  was added.
- `GET /api/issues/{id}/report` now serves only reconstructed v5 reports with
  the exact user-approved six authored fields plus deterministic relationship,
  limitation, and caution fields.
- Read-time validation reloads the linked metric/snapshot and same-episode
  verified candidates, then reruns schema, wording, unsupported-number,
  evidence-reference, URL/domain, timestamp, and deterministic-copy checks.
- V1–v4, failed, malformed, incomplete, mismatched, withheld, or source-less
  candidate bundles remain audit-only and return the neutral empty state.
- Recent successful v5 rows are checked newest-first. A malformed latest row
  cannot replace an earlier valid v5 report.

## Public contract

The response exposes `report_version="v5"`, report/data/episode timestamps,
ordered evidence references, verified candidates and exact stored source URLs,
and the strict content object. `evidence_synthesis` is null exactly when the
candidate array is empty. No internal citation ID, hash, excerpt, score, query,
model reasoning, or provider usage crosses the API boundary.

## Verification

- Backend full suite: 332 passed
- Ruff: pass
- OpenAPI exact-field test: pass
- Integrated context → verifier → v5 writer → API test: pass
- Zero-source, one-source, invalid latest row, withheld candidate, empty source,
  episode mismatch, evidence-ID mismatch, unsupported number, unsafe source
  field, URL/domain mismatch, and timestamp mismatch states: pass

