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

**Current implementation state**: routes return hardcoded sample data, not
live Postgres reads — TASK-002's schema has not been applied to any
database yet. DB wiring is a follow-up once TASK-002 is approved; response
shapes are not expected to change at that point.

## `GET /api/health`

No params. See `app/schemas/health.py::HealthResponse`.

```json
{ "status": "ok", "service": "outlook-signals-api", "time": "2026-07-08T09:00:00Z" }
```

## `GET /api/issues`

Ranked/browsable issue list.

| Param | Type | Default | Notes |
|---|---|---|---|
| `category` | string | none | exact match against `/api/categories` values |
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
(ADR-003) — and must pass the banned-phrase filter before storage.

```json
{
  "id": "7c2e1a90-0000-4000-8000-0000000000aa",
  "generated_at": "2026-07-08T09:00:00Z",
  "data_as_of": "2026-07-08T09:00:00Z",
  "status": "success",
  "content": {
    "issue_summary": "...",
    "movement_explanation": "...",
    "key_change_context": "...",
    "uncertainty_summary": "...",
    "neutral_conclusion": "..."
  }
}
```

If no report exists yet:

```json
{ "status": "not_yet_generated" }
```

`404` if `id` is unknown.

### Open item for PM sign-off

Technical Design §5 specifies "`204` with a body hint
`{"status": "not_yet_generated"}`" for the no-report-yet case. **HTTP `204
No Content` cannot carry a response body** per spec — most HTTP clients
discard it. This draft instead returns `200` with
`{"status": "not_yet_generated"}` so the frontend can read it. Flagging for
PM/Frontend confirmation before this is treated as final.

## `GET /api/categories`

```json
{ "categories": ["politics", "economy", "environment", "technology", "world"] }
```

## Error shape (all endpoints)

- `404` — unknown id, FastAPI default `{"detail": "..."}` shape (not yet
  normalized to the `ErrorResponse` schema in `app/schemas/issues.py` —
  flagged as a follow-up, low risk to change before frontend depends on it).
- `400` — invalid `window`/`sort` enum value.
- `503` — reserved for the "degrade to last-known-good data" fallback
  (Technical Design §5); not yet triggerable since there is no live DB read
  path yet.

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
