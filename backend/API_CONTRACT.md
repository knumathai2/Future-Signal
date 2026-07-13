# API Contract — Outlook AI Signals

_Status: implemented active v8 contract, 2026-07-12._

Executable schemas live in `app/schemas/issues.py` and
`app/schemas/health.py`; routes live in `app/api/routes/`. This document
describes only the implemented public contract. Superseded contracts remain
recoverable from Git history.

## Common boundaries

- All timestamps are ISO 8601 UTC.
- Public paths use issue-monitoring terminology.
- Issue/category/history reads use Postgres when configured and otherwise
  return documented timestamped fallback data.
- The generation POST appends or joins request state in Postgres. The API
  process does not call Polymarket or an AI provider.
- Report reads expose only a successful v8 row that reconstructs from its
  stored metric, snapshot, definition, context, source, claim, fingerprint,
  timing, caution, and wording evidence.
- Static fallback never fabricates a report or source.

## Endpoint summary

| Method | Path                                                   | Response                                       |
| ------ | ------------------------------------------------------ | ---------------------------------------------- |
| GET    | `/api/health`                                          | Service health                                 |
| GET    | `/api/issues`                                          | Ranked/paginated issue list                    |
| GET    | `/api/issues/{id}`                                     | Issue detail with related material and signals |
| GET    | `/api/issues/{id}/history`                             | 24h, 7d, or 30d time series                    |
| GET    | `/api/categories`                                      | Currently servable broad categories            |
| GET    | `/api/issues/{id}/report`                              | Active v8 report/generation state              |
| POST   | `/api/issues/{id}/report/generate`                     | Append or join one v8 generation request       |
| GET    | `/api/issues/{id}/report/requests/{request_id}`        | Latest request state                           |
| GET    | `/api/issues/{id}/report/requests/{request_id}/stream` | Validated-block SSE replay and live delivery   |

## `GET /api/health`

```json
{
  "status": "ok",
  "service": "outlook-signals-api",
  "time": "2026-07-12T03:00:00Z"
}
```

## `GET /api/issues`

| Parameter  | Type                          | Default | Constraint                                            |
| ---------- | ----------------------------- | ------- | ----------------------------------------------------- |
| `category` | string                        | omitted | Broad Korean category or accepted raw stored category |
| `window`   | `24h` or `7d`                 | `24h`   | Selects the comparison field                          |
| `sort`     | `heat`, `change`, or `recent` | `heat`  | Ordering rule                                         |
| `limit`    | integer                       | `20`    | 1-100                                                 |
| `offset`   | integer                       | `0`     | At least 0                                            |

```json
{
  "data_as_of": "2026-07-12T03:00:00Z",
  "issues": [
    {
      "id": "b3f1c2a4-0000-4000-8000-000000000001",
      "title": "Will the documented condition be met by the stated date?",
      "category": "정치",
      "current_value": 0.63,
      "change_24h": 0.08,
      "change_7d": 0.11,
      "confidence_level": "sufficient",
      "heat_score": 70.4
    }
  ]
}
```

`change_24h`, `change_7d`, and `heat_score` may be `null` when the required
history is unavailable. `current_value` is a reflected expectation value on a
0-1 scale.

## `GET /api/issues/{id}`

```json
{
  "id": "b3f1c2a4-0000-4000-8000-000000000001",
  "title": "Will the documented condition be met by the stated date?",
  "description": "Tracks the stated condition in public aggregate data.",
  "category": "정치",
  "status": "active",
  "outcome_label": "Yes",
  "current_value": 0.63,
  "change_24h": 0.08,
  "change_7d": 0.11,
  "confidence_level": "sufficient",
  "heat_score": 70.4,
  "data_as_of": "2026-07-12T03:00:00Z",
  "related_events": [],
  "signals": [
    {
      "signal_type": "expectation_shift",
      "severity": "medium",
      "window": "24h",
      "magnitude": 0.08,
      "triggered_at": "2026-07-12T03:00:00Z"
    }
  ]
}
```

Allowed `confidence_level` values are `sufficient`,
`caution_low_activity`, `caution_high_volatility`, and `insufficient_data`.
An unknown issue returns `404`.

## `GET /api/issues/{id}/history`

`window` is required by the public UI as `24h`, `7d`, or `30d`.

```json
{
  "data_as_of": "2026-07-12T03:00:00Z",
  "window": "7d",
  "points": [
    { "captured_at": "2026-07-11T03:00:00Z", "value": 0.58 },
    { "captured_at": "2026-07-12T03:00:00Z", "value": 0.63 }
  ]
}
```

Missing history returns an empty `points` array rather than a fabricated
latest point. An unknown issue returns `404`.

## `GET /api/categories`

Returns broad Korean labels derived from currently servable issues. A sample
fallback is used when live data is unavailable.

```json
{ "categories": ["정치", "경제", "환경", "기술", "세계"] }
```

## `GET /api/issues/{id}/report`

The endpoint returns exactly one of four shapes.

### Idle

```json
{ "status": "idle" }
```

### Generating without a previous valid report

```json
{
  "status": "generating",
  "request_id": "8d534f4a-0000-4000-8000-000000000001",
  "input_fingerprint": "64 lowercase hexadecimal characters",
  "requested_at": "2026-07-12T03:01:00Z"
}
```

### Failed without a previous valid report

```json
{
  "status": "failed",
  "request_id": "8d534f4a-0000-4000-8000-000000000001",
  "error_code": "safe_error_code"
}
```

### Full v8 report

`status` is `fresh`, `stale`, `generating`, or `failed_with_last_good`.

```json
{
  "id": "7c2e1a90-0000-4000-8000-0000000000aa",
  "status": "fresh",
  "report_version": "v8",
  "headline": "Issue-centered headline",
  "summary": "A two-to-four sentence evidence-bounded summary.",
  "sections": [
    {
      "type": "current_situation",
      "title": "Current situation",
      "format": "paragraph",
      "content": "Evidence-bounded paragraph content.",
      "items": [],
      "evidence_refs": ["market_definition:..."]
    },
    {
      "type": "recent_change",
      "title": "Recent change",
      "format": "bullets",
      "content": null,
      "items": ["Observed data statement"],
      "evidence_refs": ["metric:..."]
    }
  ],
  "sources": [],
  "generated_at": "2026-07-12T03:02:00Z",
  "data_as_of": "2026-07-12T03:00:00Z",
  "context_as_of": null,
  "cache": {
    "state": "fresh",
    "input_fingerprint": "64 lowercase hexadecimal characters",
    "current_fingerprint": "64 lowercase hexadecimal characters"
  },
  "data_limitations": "Deterministic data limitations.",
  "caution_note": "Deterministic interpretation caution.",
  "request_id": null,
  "request_error_code": null
}
```

Section `type` is one of `current_situation`, `recent_change`,
`interpretation`, `key_conditions`, `what_to_watch`, or `limitations`.
`current_situation` and `recent_change` are required. A paragraph carries
`content` only; a bullet section carries `items` only. Every section has at
least one evidence reference.

Public sources use the stored v7-compatible source schema: exact source ID,
context parent, citation ID, title, URL, domain, A-C level, one or more
supported claims, and retrieval time. Each claim carries its reference, text,
exact excerpt, and citation ID. URL/domain and source-parent checks run before
serving.

The read path checks up to the newest 20 successful v8 rows and serves the
first fully reconstructible row. A newer invalid row cannot replace an older
valid report.

## `POST /api/issues/{id}/report/generate`

Request:

```json
{ "refresh_context": true }
```

Response is HTTP `202`:

```json
{
  "request_id": "8d534f4a-0000-4000-8000-000000000001",
  "status": "queued",
  "created": true,
  "input_fingerprint": "64 lowercase hexadecimal characters"
}
```

`status` is `queued`, `running`, `fresh`, or `failed`. The API creates or joins
one immutable market/fingerprint request. In local/development environments a
queued result launches the isolated worker after the request commits.

Responses:

- `404`: unknown issue;
- `409`: the current evidence bundle is unavailable;
- `503`: generation storage is unavailable or the request write fails.

## `GET /api/issues/{id}/report/requests/{request_id}`

```json
{
  "request_id": "8d534f4a-0000-4000-8000-000000000001",
  "issue_id": "b3f1c2a4-0000-4000-8000-000000000001",
  "state": "running",
  "attempt_number": 1,
  "requested_at": "2026-07-12T03:01:00Z",
  "updated_at": "2026-07-12T03:01:02Z",
  "input_fingerprint": "64 lowercase hexadecimal characters",
  "report_id": null,
  "error_code": null,
  "successor_request_id": null
}
```

`state` is `queued`, `running`, `succeeded`, or `failed`. The request must
belong to the issue. Missing request state returns `409`; unavailable storage
returns `503`.

## `GET /api/issues/{id}/report/requests/{request_id}/stream`

Returns `text/event-stream`. It replays validated blocks for the active attempt
and follows new state until success or failure.

Event types:

- `status`: current request state and attempt;
- `block`: one stored headline/summary or section block;
- `complete`: final report identity and timing;
- `generation_error`: safe terminal error code.

Each `block` has a database event ID, attempt and sequence number, block type,
and strict payload. `Last-Event-ID` resumes after the last received block.
Connection comments are keep-alives only. Raw provider fragments are never
emitted.

## Scenario conversation

The scenario API returns `404 feature_unavailable` unless
`SCENARIO_CONVERSATION_ENABLED=true`; production generation also requires
`AI_GENERATION_WORKERS_ENABLED=true`. Both flags default to false in code. The
checked-in production Compose profile enables both explicitly. The API process
never constructs a provider client.

### `POST /api/issues/{id}/scenario-sessions`

Creates one issue-scoped, fixed 24-hour session and returns HTTP `201`. The
response contains session ID, issue ID, creation/expiry/data times, eight-turn
limit, policy version, caution, and a random 256-bit `session_capability`. The
capability is returned only here; only its hash is stored. The response uses
`Cache-Control: no-store` and `Referrer-Policy: no-referrer`.

### Owned session operations

Every later operation requires:

```text
Authorization: Bearer <session capability>
```

- `GET /api/issues/{id}/scenario-sessions/{session_id}` returns validated owned
  turns, premise classes, remaining turns, data time, and caution.
- `POST /api/issues/{id}/scenario-sessions/{session_id}/turns` requires a UUID
  `Idempotency-Key`, appends one user turn plus immutable queued request/event,
  and returns HTTP `202`. After a newly created request commits, one isolated
  worker starts when generation workers are enabled; an idempotent replay does
  not spawn a duplicate. The API process itself never calls a provider.
- `GET /api/issues/{id}/scenario-sessions/{session_id}/turns/{turn_id}` returns
  queued/running/succeeded/failed state and safe terminal metadata.
- `GET /api/issues/{id}/scenario-sessions/{session_id}/turns/{turn_id}/stream`
  uses authenticated fetch-SSE to replay only stored complete paragraph/list
  blocks. The first available block is immediate and subsequent blocks are
  paced in sequence for progressive rendering. Capabilities are forbidden in
  URLs; raw provider chunks are never events.
- `DELETE /api/issues/{id}/scenario-sessions/{session_id}` returns `204` and
  hard-deletes only the authenticated ephemeral scenario graph.

Unknown, mismatched, expired, deleted, and wrong-capability sessions return the
same non-enumerating `404 session_unavailable` code. A missing/malformed bearer
header returns `401 session_token_required`. Fixed message/session/in-flight/
rate limits return safe `409`, `413`, or `429` codes. Storage/current-bundle
failure returns `409` or `503` without provider or database detail.

Migration 006 must be applied before enabling this API. The request-scoped
worker uses no model tools and stores only a completely validated assistant turn
and paragraph/list blocks.

Authenticated status and SSE reads may relaunch only a request that has remained
`queued` at attempt zero for at least five seconds. Relaunch uses a process-local
20-second cooldown and three-launch cap. The worker locks the immutable request
row before changing it to `running`, so concurrent child processes cannot create
duplicate provider calls. Running, succeeded, and failed attempts are not
automatically retried.

## Validation and fallback

- Invalid enum/query values use FastAPI's `422` detail response.
- Unknown issue/request identities use `404`.
- Issue/category/history reads degrade to timestamped fallback data with HTTP
  `200` when live data is unavailable.
- Generation writes do not use static fallback and may return `409` or `503`.
- A failed writer attempt never replaces the previous valid v8 report.
- Every public report retains data timing, deterministic limitations, and
  interpretation caution.
- Active wording and source rules are defined by `memory/glossary.md`,
  `standards.md`, Service Design, and UX Design; this API does not weaken them.

## Version scope

Only the active v8 report contract and current scenario API are documented
here. Superseded response examples and prompt shapes are available from Git
history and are not public compatibility commitments.
