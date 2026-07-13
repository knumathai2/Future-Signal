# Technical Design: API Structure and Batch Collection

_Source: former project-root Technical Design sections 5-6._

---

## 5. API Structure

Issue-data endpoints are read-only. Public write paths append briefing requests
or capability-owned scenario state; neither calls a provider in the API
process. The API uses REST/JSON under the versionless `/api` prefix.

| Endpoint                                             | Method | Purpose                                                              | Key params                                                                    | DB tables used                                                   | MVP priority                          |
| ---------------------------------------------------- | ------ | -------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------- |
| `/api/issues`                                        | GET    | Ranked/browsable issue list                                          | `category`, `window` (24h/7d), `sort` (heat/change/recent), `limit`, `offset` | `markets`, `market_metrics`                                      | **P0**                                |
| `/api/issues/:id`                                    | GET    | Full issue detail                                                    | —                                                                             | `markets`, `market_outcomes`, `market_metrics`, `related_events` | **P0**                                |
| `/api/issues/:id/history`                            | GET    | Time series for chart                                                | `window` (24h/7d/30d)                                                         | `market_snapshots`                                               | **P0**                                |
| `/api/issues/:id/report`                             | GET    | V8 idle/generating/fresh/stale/failure state and latest valid report | —                                                                             | `ai_reports`, generation requests/events, evidence tables        | **P0**                                |
| `/api/issues/:id/report/generate`                    | POST   | Create or join a fingerprinted generation request; no provider call  | `refresh_context`                                                             | generation requests/events, evidence tables                      | **P0 v8**                             |
| `/api/issues/:id/report/requests/:request_id`        | GET    | Poll append-only request/lease/outcome state                         | —                                                                             | generation requests/events                                       | **P0 v8**                             |
| `/api/issues/:id/report/requests/:request_id/stream` | GET    | Replay and follow only validated v8 blocks as SSE                    | `Last-Event-ID` header                                                        | generation requests/events/blocks                                | **P0 v8**                             |
| `/api/categories`                                    | GET    | List of categories for filter UI                                     | —                                                                             | `markets` (distinct)                                             | **P0**                                |
| `/api/health`                                        | GET    | Uptime/monitoring check                                              | —                                                                             | none (or a trivial `SELECT 1`)                                   | **P0**, trivial to build, do it early |

### Example: `GET /api/issues?window=24h&sort=heat&limit=10`

```json
{
  "data_as_of": "2026-07-07T09:00:00Z",
  "issues": [
    {
      "id": "b3f1...",
      "title": "Will [event] be resolved as Yes by [date]?",
      "category": "politics",
      "current_value": 0.63,
      "change_24h": 0.082,
      "change_7d": 0.11,
      "confidence_level": "sufficient",
      "heat_score": 78.4
    }
  ]
}
```

### Error cases (applies across all endpoints)

- `404` — unknown `market_id`.
- `422` — invalid enum/query values using FastAPI's validated error response.
- `409` — current evidence, request, or owned-session state cannot satisfy the
  requested operation.
- `503` — generation storage is unavailable. Read endpoints degrade to honest
  timestamped fallback or last-known-good states where applicable.
- A missing briefing returns HTTP `200` with `{"status": "idle"}`.

### Naming discipline

Every path uses `issues`, `signals`, `reports`, `categories` — never `markets` in the public-facing path even though the DB table is named `markets` internally (an internal DB name is fine; the _API surface_ is the part users' browsers see in network tabs, and `issues` reinforces the product framing from UX Design). No `/bets`, `/trades`, `/positions`, `/profits` anywhere, including in internal code — naming leaks into product framing over time even when it's "just" a variable name.

### 5.1 Scenario-conversation API

The following interface is disabled by default in application code and enabled
when `SCENARIO_CONVERSATION_ENABLED=true`. Production generation also requires
`AI_GENERATION_WORKERS_ENABLED=true`; the checked-in production Compose profile
sets both explicitly.

| Endpoint                                                              | Method | Purpose                                                                                |
| --------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------- |
| `/api/issues/:id/scenario-sessions`                                   | POST   | Create one issue-scoped, fixed-expiry anonymous session and return its capability once |
| `/api/issues/:id/scenario-sessions/:session_id`                       | GET    | Read only the caller-owned validated session state                                     |
| `/api/issues/:id/scenario-sessions/:session_id/turns`                 | POST   | Append one bounded user turn with bearer capability and idempotency key                |
| `/api/issues/:id/scenario-sessions/:session_id/turns/:turn_id`        | GET    | Read caller-owned queued/running/succeeded/failed turn state                           |
| `/api/issues/:id/scenario-sessions/:session_id/turns/:turn_id/stream` | GET    | Replay complete validated blocks progressively through authenticated fetch-SSE         |
| `/api/issues/:id/scenario-sessions/:session_id`                       | DELETE | Invalidate the capability and request ephemeral-content deletion                       |

The session ID never grants access. Every operation except creation requires a
256-bit bearer capability whose hash alone is stored. The capability is never
placed in a URL. The Frontend uses `fetch` streaming so the authorization and
`Last-Event-ID` headers remain available; native `EventSource` is not used.
Stored blocks are materialized and the read transaction is released before
delivery. The first block is immediate; remaining blocks are paced in sequence.
Raw provider fragments never cross the public API boundary.

The API validates issue/session ownership, expiry, fixed limits, one in-flight
turn, idempotency, current input fingerprint, and local request ceilings before
appending a request. It never constructs a provider client. Safe public errors
do not distinguish unknown, mismatched, expired, deleted, or unauthorized
sessions in a way that permits enumeration.

One detached request-scoped worker starts after a newly created turn commits;
idempotent replay does not spawn a duplicate. The API process still constructs
no provider client. The Frontend uses authenticated fetch-SSE, strict response
parsing, restricted rendering, sessionStorage recovery, and polling fallback.

Only attempt-zero rows still queued after five seconds are eligible for bounded
recovery. Authenticated status/SSE access triggers relaunch through a 20-second
process-local cooldown and three-launch cap. The worker row-locks the request
before appending `running`, preventing duplicate provider work. Running or
terminal attempts never enter this recovery path.

---

## 6. Collection and Worker Pipelines

### 6.1 Scheduled market-data collection

GitHub Actions runs the collection workflow every four hours at minute 17 UTC.
The sequential Python batch performs:

1. Fetch public Gamma records with bounded pagination and retry.
2. Normalize active binary issues and quarantine malformed records.
3. Persist market/outcome identity and append a new snapshot.
4. Calculate fixed 24-hour and 7-day changes from eligible historical points.
5. Append metrics, change signals, and collection status.
6. Skip context research and briefing generation explicitly.

The workflow receives database configuration only. It does not receive provider
credentials.

### 6.2 Briefing request flow

```text
POST request
  -> reconstruct current evidence bundle
  -> append/join immutable fingerprinted request
  -> launch isolated worker when enabled
  -> claim lease
  -> optional bounded context refresh
  -> one validated NDJSON response
  -> append complete blocks
  -> append final v8 report and success event
  -> SSE replay or polling
```

A failed attempt appends a safe terminal event, removes partial public output,
and preserves the previous valid report. Expired-running leases may be claimed
again; manual recovery can target one exact request ID.

### 6.3 Scenario request flow

```text
capability-authenticated turn
  -> validate session, limits, fingerprint, and idempotency
  -> append immutable turn request
  -> launch isolated worker when enabled
  -> build typed issue/evidence/premise bundle
  -> one tool-free provider call
  -> validate complete output and blocks
  -> append assistant turn and terminal event
  -> authenticated SSE replay or polling
```

Attempt-zero queued requests may be relaunched only through the bounded
status/SSE recovery path. Running and terminal attempts do not retry
automatically.

### 6.4 Failure handling

- Read failures return timestamped fallback or honest empty states.
- Invalid public input fails through FastAPI/Pydantic validation.
- Source, evidence, wording, numeric, leakage, Markdown, or schema failure blocks
  storage and publication.
- Provider usage and safe failure metadata are recorded without prompts,
  responses, capabilities, or secrets.
- Production-data writes, provider changes, migrations, deployment, and
  infrastructure changes follow `AGENTS.md`.
