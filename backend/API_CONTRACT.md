# API Contract Draft — Outlook Signals

_Status: draft, for PM/Frontend review (TASK-003). Source of truth for scope is
[Technical Design §5](../docs/tech-design/03-api-and-batch-pipeline.md); this
document concretizes exact field names/types and is backed by runnable
Pydantic schemas (`app/schemas/issues.py`, `app/schemas/health.py`) and mock
routes (`app/api/routes/`) so the shapes below are checkable via
`GET /openapi.json` or `/docs`, not just prose._

**All endpoints are read-only.** All timestamps are ISO 8601 UTC. Public
paths use `issues` / `signals` / `reports` / `categories` — never `markets`,
`bets`, `trades`, `positions`, or `profits` (enforced by
`tests/test_issues_contract.py::test_public_paths_never_use_market_terminal_vocabulary`).

**Current implementation state** (TASK-010/TASK-039): issue and history routes
read from Postgres via `app/db/session.py::get_db()` when `DATABASE_URL` is
set and live `market_snapshots` data exists. The report route reads the latest
successful stored `ai_reports` row in live mode and otherwise preserves the
accepted empty state. TASK-002's schema is still unapplied to any
shared/production database. Response shapes did not change from the earlier
mock-only draft.

## `GET /api/health`

No params. See `app/schemas/health.py::HealthResponse`.

```json
{ "status": "ok", "service": "outlook-signals-api", "time": "2026-07-08T09:00:00Z" }
```

## `GET /api/issues`

Ranked/browsable issue list.

| Param | Type | Default | Notes |
|---|---|---|---|
| `category` | string | none | match against `/api/categories` Korean display values; raw stored category values are also accepted for backward compatibility |
| `window` | enum `24h`\|`7d` | `24h` | which change field ranking/`sort=change` uses |
| `sort` | enum `heat`\|`change`\|`recent` | `heat` | |
| `limit` | int 1-100 | 20 | |
| `offset` | int ≥0 | 0 | |

```json
{
  "data_as_of": "2026-07-08T09:00:00Z",
  "issues": [
    {
      "id": "b3f1c2a4-0000-4000-8000-000000000001",
      "title": "Will the proposed climate accord be ratified by December 2026?",
      "category": "environment",
      "current_value": 0.63,
      "change_24h": 0.082,
      "change_7d": 0.11,
      "confidence_level": "sufficient",
      "heat_score": 78.4
    }
  ]
}
```

## `GET /api/issues/{id}`

Full issue detail, including embedded related-event candidates and signals
(Technical Design §5 notes both can be folded into detail for MVP instead of
separate calls — done here).

```json
{
  "id": "b3f1c2a4-0000-4000-8000-000000000001",
  "title": "Will the proposed climate accord be ratified by December 2026?",
  "description": "Tracks reflected expectation on ratification of the multilateral climate accord.",
  "category": "environment",
  "status": "active",
  "outcome_label": "Yes",
  "current_value": 0.63,
  "change_24h": 0.082,
  "change_7d": 0.11,
  "confidence_level": "sufficient",
  "heat_score": 78.4,
  "data_as_of": "2026-07-08T09:00:00Z",
  "related_events": [
    { "event_title": "...", "event_date": "2026-07-01T00:00:00Z", "note": "A related event candidate, not a cause: ..." }
  ],
  "signals": [
    { "signal_type": "expectation_shift", "severity": "medium", "window": "24h", "magnitude": 0.082, "triggered_at": "2026-07-08T09:00:00Z" }
  ]
}
```

`404` if `id` is unknown.

## `GET /api/issues/{id}/history?window=24h|7d|30d`

```json
{
  "data_as_of": "2026-07-08T09:00:00Z",
  "window": "7d",
  "points": [{ "captured_at": "2026-07-08T09:00:00Z", "value": 0.63 }]
}
```

`404` if `id` is unknown.

## `GET /api/issues/{id}/report`

Latest AI report. Content is fixed template slots only — never free-form
(ADR-003, updated by ADR-028) — and must pass the banned-phrase filter before
storage.
When live data is available, the API serves the latest `status="success"`
`ai_reports` row for the issue using the current prompt version. Failed rows
and legacy prompt-version rows are retained in storage but are not returned
from this endpoint. Stored current-version content that does not match the
current schema is treated as not yet generated rather than partially served.

```json
{
  "id": "7c2e1a90-0000-4000-8000-0000000000aa",
  "generated_at": "2026-07-08T09:00:00Z",
  "data_as_of": "2026-07-08T09:00:00Z",
  "status": "success",
  "content": {
    "issue_explainer": "...",
    "why_it_matters": "...",
    "current_reading": "...",
    "scenario_major_change": "...",
    "scenario_limited_change": "...",
    "scenario_status_quo": "...",
    "check_points": "...",
    "caution_note": "..."
  }
}
```

If no report exists yet:

```json
{ "status": "not_yet_generated" }
```

`404` if `id` is unknown.

Per ADR-008, this returns `200` with `{"status": "not_yet_generated"}`
rather than Technical Design §5's originally proposed `204` (HTTP `204 No
Content` cannot carry a body per spec, so most clients would discard the
hint). This is accepted as final, not an open item.

## `GET /api/categories`

When live issue data is available, this returns Korean display categories for
currently servable issues. These can be broader or more recognizable than the
stored source tags, for example `우크라이나 전쟁`, `이란 전쟁`, `미국 정치`,
or `가상자산`. In DB-free/static fallback mode, it returns the sample category
list below.

```json
{ "categories": ["환경", "경제"] }
```

## Error shape (all endpoints)

- `404` — unknown id, FastAPI default `{"detail": "..."}` shape (not yet
  normalized to the `ErrorResponse` schema in `app/schemas/issues.py` —
  flagged as a follow-up, low risk to change before frontend depends on it).
- `422` — invalid `window`/`sort` enum value. (This document previously said
  `400`; FastAPI's built-in `Query(pattern=...)` validation — which
  TASK-010 preserves unchanged — returns `422` with
  `{"detail": [...]}`, not `400`. Flagged as a pre-existing doc/implementation
  mismatch, not a TASK-010 regression; see `memory/known-issues.md`.)
- **No `503`.** TASK-010 implements the "degrade to last-known-good data"
  requirement (Technical Design §5, PRD §8.1) as `200` with the static
  sample dataset and an honest `data_as_of`, not a `503`, so the dashboard
  never has to render a hard-error state during a demo. This applies when
  `DATABASE_URL` is unset or unreachable, or when no `market_snapshots` rows
  exist yet (e.g. TASK-008 has not run) — see the FALLBACK NOTE in
  `app/api/routes/issues.py` and `reports/task-010-core-api-notes.md`.

## Wording alignment with `memory/glossary.md`

- `current_value` = "reflected expectation value" (never `price` or
  `probability` in the public API).
- `confidence_level` keeps its internal DB-aligned name in the JSON payload;
  the frontend is expected to display it as "Data reliability" per the
  glossary's use-carefully guidance — this API does not send display copy,
  only the raw enum.
- `related_events[].note` must always carry the "candidate, not cause"
  qualifier — enforced by convention here, not yet by a runtime filter
  (the banned-phrase filter itself is Data/AI scope, Service Design §6).
