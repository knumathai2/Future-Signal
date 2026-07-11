# Technical Design: API Structure and Batch Collection

_Source: former project-root Technical Design sections 5-6._

---

## 5. API Structure

All endpoints are **read-only** in MVP except the internal report-trigger, which is not user-facing. REST, JSON, versionless for hackathon (`/api/...` prefix is enough, no `/v1` needed yet).

| Endpoint | Method | Purpose | Key params | DB tables used | MVP priority |
|---|---|---|---|---|---|
| `/api/issues` | GET | Ranked/browsable issue list | `category`, `window` (24h/7d), `sort` (heat/change/recent), `limit`, `offset` | `markets`, `market_metrics` | **P0** |
| `/api/issues/:id` | GET | Full issue detail | — | `markets`, `market_outcomes`, `market_metrics`, `related_events` | **P0** |
| `/api/issues/:id/history` | GET | Time series for chart | `window` (24h/7d/30d) | `market_snapshots` | **P0** |
| `/api/issues/:id/metrics` | GET | Full metric breakdown (if not already folded into detail) | — | `market_metrics` | **P1** (can fold into detail response for MVP instead of a separate call) |
| `/api/signals` | GET | Recent signals across all markets ("what changed recently" feed) | `severity`, `since` | `issue_signals`, `markets` | **P1** |
| `/api/issues/:id/signals` | GET | Signals for one market | — | `issue_signals` | **P0** (can be embedded in detail response) |
| `/api/issues/:id/report` | GET | Latest AI report for the issue | — | `ai_reports` | **P0** |
| `/api/issues/:id/report/generate` | POST (internal only, not called by the frontend) | Force regeneration; used by the batch job or an admin/demo script, never exposed as a user-facing button per UX Design §3.6 | — | `ai_reports`, `market_metrics` | **P1** (useful for demo-prep to guarantee the 3 demo issues have fresh reports) |
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
| 8. Trigger AI report generation only when needed | Markets with a new signal from step 6, OR no existing report, OR last report older than a set staleness window (e.g., 24h) | Call `generate_report()` (Section 9) per qualifying market, capped at a max count per run for cost control | Insert into `ai_reports` | AI API error → retry once, mark `status=failed`, leave the previous successful report as the one served to users | Isolate each market's report generation in its own try/except so one AI failure doesn't block others |

### Sync vs. async
- **Steps 1–7 run synchronously, in sequence, within one script invocation.** There's no benefit to parallelizing or queueing this for 30–50 markets — the whole run should complete in well under a minute, and sequential code is far easier to debug under hackathon time pressure.
- **Step 8 (AI generation) is asynchronous relative to any user request** — it never runs in response to an API call, only from the batch job. Within the batch job itself, it can still execute sequentially at the end of the run; "asynchronous" here means "decoupled from the request/response cycle," not "requires a job queue." A real async queue (Celery/RQ, or a `pending`-status polling worker) is a legitimate Phase 2 upgrade once report volume or generation latency grows enough to matter.

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

---
