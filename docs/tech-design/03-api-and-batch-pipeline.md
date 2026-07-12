# Technical Design: API Structure and Batch Collection

_Source: former project-root Technical Design sections 5-6._

---

## 5. API Structure

All issue-data endpoints are read-only. ADR-051 adds one public append-only
generation-request POST; it never calls a provider in the API process. REST,
JSON, versionless for hackathon (`/api/...` prefix is enough, no `/v1` needed yet).

| Endpoint | Method | Purpose | Key params | DB tables used | MVP priority |
|---|---|---|---|---|---|
| `/api/issues` | GET | Ranked/browsable issue list | `category`, `window` (24h/7d), `sort` (heat/change/recent), `limit`, `offset` | `markets`, `market_metrics` | **P0** |
| `/api/issues/:id` | GET | Full issue detail | — | `markets`, `market_outcomes`, `market_metrics`, `related_events` | **P0** |
| `/api/issues/:id/history` | GET | Time series for chart | `window` (24h/7d/30d) | `market_snapshots` | **P0** |
| `/api/issues/:id/metrics` | GET | Full metric breakdown (if not already folded into detail) | — | `market_metrics` | **P1** (can fold into detail response for MVP instead of a separate call) |
| `/api/signals` | GET | Recent signals across all markets ("what changed recently" feed) | `severity`, `since` | `issue_signals`, `markets` | **P1** |
| `/api/issues/:id/signals` | GET | Signals for one market | — | `issue_signals` | **P0** (can be embedded in detail response) |
| `/api/issues/:id/report` | GET | V8 idle/generating/fresh/stale/failure state and latest valid report | — | `ai_reports`, generation requests/events, evidence tables | **P0** |
| `/api/issues/:id/report/generate` | POST | Create or join a fingerprinted generation request; no provider call | `refresh_context` | generation requests/events, evidence tables | **P0 v8** |
| `/api/issues/:id/report/requests/:request_id` | GET | Poll append-only request/lease/outcome state | — | generation requests/events | **P0 v8** |
| `/api/issues/:id/report/requests/:request_id/stream` | GET | Replay and follow only validated v8 blocks as SSE | `Last-Event-ID` header | generation requests/events/blocks | **P0 v8** |
| `/api/categories` | GET | List of categories for filter UI | — | `markets` (distinct) | **P1** |
| `/api/search` | GET | Simple title search | `q` | `markets` (ILIKE) | **P2** |
| `/api/watchlist` | GET/POST/DELETE | Phase 2 only | `market_id` | `watchlists` | **Excluded from MVP** |
| `/api/health` | GET | Uptime/monitoring check | — | none (or a trivial `SELECT 1`) | **P0**, trivial to build, do it early |

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
- `400` — invalid `window`/`sort` value (return the allowed enum in the error body).
- `503` with the **last known good** payload still served where possible (e.g., `/api/issues` should degrade to cached/last-successful data rather than a hard failure) — matches PRD §8.1's fallback requirement, and should be enforced at the API layer (read the most recent `market_metrics` row per market regardless of exact staleness, and surface `data_as_of` honestly) rather than only at the batch layer.
- AI report specifically: if no report exists yet for a market, `GET /api/issues/:id/report` returns `204` (not `404`) with a body hint like `{"status": "not_yet_generated"}`, so the frontend can show a neutral empty state instead of an error.

### Naming discipline
Every path uses `issues`, `signals`, `reports`, `categories` — never `markets` in the public-facing path even though the DB table is named `markets` internally (an internal DB name is fine; the *API surface* is the part users' browsers see in network tabs, and `issues` reinforces the product framing from UX Design). No `/bets`, `/trades`, `/positions`, `/profits` anywhere, including in internal code — naming leaks into product framing over time even when it's "just" a variable name.

### 5.1 Approved default-off scenario-conversation API (TASK-126)

The following approved interface is implemented behind
`SCENARIO_CONVERSATION_ENABLED=false` by default and an additional
local/development environment guard:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/issues/:id/scenario-sessions` | POST | Create one issue-scoped, fixed-expiry anonymous session and return its capability once |
| `/api/issues/:id/scenario-sessions/:session_id` | GET | Read only the caller-owned validated session state |
| `/api/issues/:id/scenario-sessions/:session_id/turns` | POST | Append one bounded user turn with bearer capability and idempotency key |
| `/api/issues/:id/scenario-sessions/:session_id/turns/:turn_id` | GET | Read caller-owned queued/running/succeeded/failed turn state |
| `/api/issues/:id/scenario-sessions/:session_id/turns/:turn_id/stream` | GET | Replay complete validated blocks progressively through authenticated fetch-SSE |
| `/api/issues/:id/scenario-sessions/:session_id` | DELETE | Invalidate the capability and request ephemeral-content deletion |

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

TASK-132 starts one detached request-scoped worker after a newly created local/
development turn commits; idempotent replay does not spawn a duplicate. The API
process still constructs no provider client. TASK-129 provides the separate
default-off Frontend using authenticated fetch-SSE, strict response parsing,
restricted rendering, sessionStorage recovery, and polling fallback. Shared
infrastructure, deployment, and production activation remain gated.

TASK-134 adds bounded recovery for child processes that exit before claiming a
scenario request. Only attempt-zero rows still queued after five seconds are
eligible; authenticated status/SSE access triggers relaunch through a
20-second process-local cooldown and three-launch cap. The worker row-locks the
request before appending `running`, preventing duplicate provider work. Running
or terminal attempts never enter this recovery path.

---

## 6. Batch Data Collection Architecture

Runs as a single sequential Python script, triggered on a schedule (recommend every 1–4 hours for a 5-day hackathon — frequent enough to show real movement, infrequent enough to stay well within Polymarket's public rate limits and keep the demo dataset simple to reason about).

| Step | Input | Process | Output | Failure handling | MVP approach |
|---|---|---|---|---|---|
| 1. Fetch public market data | List of tracked `polymarket_condition_id`s (curated 30–50 set) or a filtered query against the Gamma API | HTTP GET with pagination; respect rate limits with a small delay between requests | Raw JSON per market | Timeout/5xx → exponential backoff retry (e.g., 3 attempts); after final failure, skip that market this run and log it | Simple `requests`/`httpx` loop; hardcode the curated market list for MVP rather than building dynamic discovery |
| 2. Normalize raw data | Raw JSON | Map source fields to internal schema (title, description, category, outcomes, dates, status, volume, liquidity); validate required fields present and typed correctly | Normalized market objects (Pydantic models) | Missing/malformed field → quarantine that record (log + skip), never crash the whole run over one bad market | Pydantic model with required fields; anything that fails validation gets logged to `data_collection_logs.error_detail` and skipped |
| 3. Compare with previous snapshot | Normalized current data + most recent row per market from `market_snapshots` | Compute raw deltas (price, volume, liquidity) ahead of formal metric calculation | Delta object per market | No previous snapshot exists (new market) → treat as baseline only, mark downstream metrics `insufficient_data` | Simple SQL `SELECT ... ORDER BY captured_at DESC LIMIT 1` per market |
| 4. Store current snapshot | Normalized market + delta | Insert into `market_snapshots` | New snapshot row per market | DB write error → retry once, then log and skip that market for the rest of this run (its metrics simply won't update this cycle) | Batched `INSERT` |
| 5. Calculate metrics | Current snapshot + trailing 24h/7d history from `market_snapshots` | Compute `change_24h`, `change_7d`, and (if time allows) volatility/attention/heat per Service Design §5 formulas | Insert into `market_metrics` | Fewer data points than the window requires → set the relevant field `null` and `confidence_level = insufficient_data`, never fabricate a number | Straightforward SQL/pandas over the last N rows per market |
| 6. Detect sudden change signals | Latest `market_metrics` row + threshold config | Evaluate `|change_24h| >= 5pp` (MVP threshold from PRD §8.6); check a cooldown window so the same shift doesn't refire every run | Insert into `issue_signals` if triggered | Threshold misconfiguration → fail safe to "no signal" rather than over-firing | Simple conditional; cooldown = "don't insert a new signal for the same market within the same rolling window that's already covered by an unresolved one" |
| 7. Save collection logs | Run metadata | Aggregate counts (processed/failed) and any error details from steps 1–6 | Insert into `data_collection_logs` | Logging itself failing should never fail the run — wrap in try/except with a stdout fallback | One row per run |
| Historical v1-v6 step 8 (superseded by ADR-051) | Previously selected new-signal, missing, or stale reports | Historical batch generators remain for audit/development comparison only | Historical `ai_reports` rows | Previous valid row remains | Normal collection no longer invokes this step |

### Sync vs. async
- **Steps 1–7 run synchronously, in sequence, within one script invocation.** Normal collection completes without a report provider.
- **V8 briefing generation is a separate asynchronous service.** A user request creates or joins an immutable fingerprint request, and a standalone worker claims it through an append-only expiring lease. No new queue dependency is required.

### Duplicate prevention
Since every step is append-only per run and keyed by `(market_id, captured_at)`/`(market_id, computed_at)`, duplicate prevention is really "don't run the batch job twice concurrently" — enforce with a simple advisory lock or a `data_collection_logs` check ("is there a run with `run_finished_at IS NULL` from the last hour? if so, skip") rather than building real distributed-lock infrastructure.

### Rate limit handling
Add a small fixed delay between requests (e.g., 200–500ms) and respect any `Retry-After` header Polymarket returns; with only 30–50 markets checked every 1–4 hours, this is unlikely to be a binding constraint, but building the delay in from day one avoids a last-minute scramble if it becomes one.

### 6.1 Approved v4 batch insertion point

TASK-060 inserts `context research and verification` after expectation-shift
detection and before v4 report generation. The step selects only new-signal,
absolute-change-threshold, top-10-heat, or stale/missing-candidate issues; a
first local/development backfill may process the full 30-50 issue set once.

Per issue, the hard bounds are six search queries, 30 citation results, eight
rule-passing candidates, five verifier inputs, three verified stored/public
candidates, and one research + one verifier + one writer call. One malformed
schema correction is allowed; safety or semantic failures are not retried with
the same input.

Each issue uses an isolated transaction. Provider or issue-level failure cannot
stop the full batch and cannot replace a prior successful candidate/report.
`no_candidate` is recorded as a normal completed state. Model/search/token/cost
usage is audited and the cumulative TASK-056~065 OpenRouter spend must remain
within USD 100. The batch is guarded to local/development writes until separate
deployment and production-write approval exists.

### 6.2 Approved v8 workflow separation and worker (TASK-104/TASK-112)

Normal `run_scheduled_batch()` stores market data, metrics, signals, optional
independent context, and its collection log, then exits with zero report calls.
Supplying a legacy writer client cannot make the normal path invoke it.
Historical `--reports-only` remains only as an explicitly confirmed local/dev
comparison path pending TASK-109 review.

`enqueue_v8_request()` reconstructs current definition/metric/context evidence,
computes the versioned SHA-256 fingerprint, and creates or joins one immutable
request. `process_v8_request()` claims a lease, optionally invokes a bounded
context-refresh callback, rebuilds and compares the fingerprint, makes one
writer call, validates references and language, appends a v8 report, and
appends success or safe failure. It never retries the same prompt automatically.

`run_pending_v8_requests()` is the standalone FIFO worker boundary. A crashed
worker leaves an expiring running event; a later worker appends a new attempt.
The guarded local/development CLI is `python -m app.core.on_demand_worker`.
TASK-110 connects a queued POST to that same boundary by spawning a detached,
request-scoped child with `--request-id`. The API returns immediately and never
constructs a provider client; the child owns the lease, provider call, and
append-only report/event writes. The environment guard prevents this local/dev
convenience path from silently becoming an unapproved production worker.

---
