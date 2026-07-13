# Technical Design: Database Schema Design

_Source: former project-root Technical Design sections 4-4._

---

## 4. Database Schema Design

All tables below use `bigint`/`uuid` primary keys as noted; timestamps are `timestamptz`. MVP-required tables are marked; Phase 2-only tables are clearly separated.

### 4.1 `markets` (MVP, required)

| Column                    | Type                  | Notes                                                                                |
| ------------------------- | --------------------- | ------------------------------------------------------------------------------------ |
| `id`                      | uuid, PK              | internal id                                                                          |
| `polymarket_condition_id` | text, unique, indexed | external id, used for API calls                                                      |
| `title`                   | text                  | market question                                                                      |
| `description`             | text                  |                                                                                      |
| `category`                | text, indexed         | normalized category (manual mapping if source tags are messy, per Service Design §2) |
| `outcome_type`            | text                  | `binary` only for MVP                                                                |
| `status`                  | text, indexed         | `active` / `closed` / `resolved`                                                     |
| `market_created_at`       | timestamptz           | source creation date                                                                 |
| `end_date`                | timestamptz, indexed  | resolution date                                                                      |
| `first_seen_at`           | timestamptz           | when our system first collected it                                                   |
| `last_seen_at`            | timestamptz           | last successful collection                                                           |

Relationship: parent to `market_outcomes`, `market_snapshots`, `market_metrics`, `issue_signals`, `ai_reports`.

### 4.2 `market_outcomes` (MVP, required)

| Column          | Type                   | Notes                                                                                                                |
| --------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `id`            | uuid, PK               |                                                                                                                      |
| `market_id`     | uuid, FK -> markets.id |                                                                                                                      |
| `outcome_label` | text                   | e.g. "Yes"                                                                                                           |
| `token_id`      | text                   | CLOB token id, used to fetch price history                                                                           |
| `is_tracked`    | boolean                | which outcome's price is treated as "the" expectation value for binary markets (always true for the Yes side in MVP) |

### 4.3 `market_snapshots` (MVP, required — append-only, highest write volume)

| Column         | Type                                               | Notes                          |
| -------------- | -------------------------------------------------- | ------------------------------ |
| `id`           | bigint, PK                                         |                                |
| `market_id`    | uuid, FK -> markets.id, indexed with `captured_at` |                                |
| `captured_at`  | timestamptz, indexed                               | batch run timestamp            |
| `price`        | numeric(5,4)                                       | current expectation value, 0–1 |
| `volume_24h`   | numeric                                            |                                |
| `volume_total` | numeric                                            |                                |
| `liquidity`    | numeric                                            |                                |
| `best_bid`     | numeric                                            | nullable                       |
| `best_ask`     | numeric                                            | nullable                       |

Index: composite `(market_id, captured_at DESC)` — this is the query pattern for every chart and every metric calculation.

### 4.4 `market_metrics` (MVP, required — one row per market per batch run)

| Column             | Type                                               | Notes                                                                                                                                  |
| ------------------ | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `id`               | bigint, PK                                         |                                                                                                                                        |
| `market_id`        | uuid, FK -> markets.id, indexed with `computed_at` |                                                                                                                                        |
| `computed_at`      | timestamptz                                        |                                                                                                                                        |
| `change_24h`       | numeric                                            | percentage points                                                                                                                      |
| `change_7d`        | numeric                                            | nullable if market <7d old                                                                                                             |
| `volatility_score` | numeric                                            | nullable, P1                                                                                                                           |
| `attention_score`  | numeric                                            | nullable, P1                                                                                                                           |
| `heat_score`       | numeric, indexed                                   | used for the home dashboard ranking                                                                                                    |
| `confidence_level` | text                                               | `sufficient` / `caution_low_activity` / `caution_high_volatility` / `insufficient_data` (Service Design §5 caution badge, generalized) |

### 4.5 `issue_signals` (MVP, required — sparse, only rows when a signal fires)

| Column         | Type                                                | Notes                                                                         |
| -------------- | --------------------------------------------------- | ----------------------------------------------------------------------------- |
| `id`           | bigint, PK                                          |                                                                               |
| `market_id`    | uuid, FK -> markets.id, indexed with `triggered_at` |                                                                               |
| `signal_type`  | text                                                | MVP: `expectation_shift` only; Phase 2: `attention_spike`, `unusual_activity` |
| `severity`     | text                                                | `low` / `medium` / `high` / `critical`                                        |
| `window`       | text                                                | e.g. `24h`                                                                    |
| `magnitude`    | numeric                                             | the pp change that triggered it                                               |
| `triggered_at` | timestamptz                                         |                                                                               |
| `detail`       | jsonb                                               | free-form extra context (e.g., which snapshot ids bound the window)           |

### 4.6 `ai_reports` (MVP, required)

| Column             | Type                                                | Notes                                                              |
| ------------------ | --------------------------------------------------- | ------------------------------------------------------------------ |
| `id`               | uuid, PK                                            |                                                                    |
| `market_id`        | uuid, FK -> markets.id, indexed with `generated_at` |                                                                    |
| `generated_at`     | timestamptz                                         |                                                                    |
| `input_metrics_id` | bigint, FK -> market_metrics.id                     | traceability: which metric snapshot this report was generated from |
| `content`          | jsonb                                               | structured sections (Section 10.3)                                 |
| `model_used`       | text                                                |                                                                    |
| `prompt_version`   | text                                                | for reproducibility/debugging                                      |
| `status`           | text                                                | `success` / `failed`                                               |

### 4.7 `related_events` (MVP, required for the 3–5 curated demo issues per PRD §8.9)

| Column        | Type                   | Notes                             |
| ------------- | ---------------------- | --------------------------------- |
| `id`          | uuid, PK               |                                   |
| `market_id`   | uuid, FK -> markets.id |                                   |
| `event_title` | text                   |                                   |
| `event_date`  | timestamptz            |                                   |
| `note`        | text                   | manually written context sentence |

### 4.8 `data_collection_logs` (MVP, required)

| Column              | Type        | Notes                            |
| ------------------- | ----------- | -------------------------------- |
| `id`                | bigint, PK  |                                  |
| `run_started_at`    | timestamptz |                                  |
| `run_finished_at`   | timestamptz |                                  |
| `status`            | text        | `success` / `partial` / `failed` |
| `markets_processed` | int         |                                  |
| `markets_failed`    | int         |                                  |
| `error_detail`      | jsonb       | nullable                         |

### 4.9 Phase 2 tables (not built in hackathon MVP)

| Table        | Purpose                                                                                                                                                                                         | MVP status            |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `users`      | Minimal identity for watchlist ownership — recommend just `id`, `email` (nullable if anonymous/device-id auth is chosen per UX Design §14 open question), `created_at`. No other personal data. | **Excluded from MVP** |
| `watchlists` | `id`, `user_id` FK, `market_id` FK, `created_at`, unique `(user_id, market_id)`                                                                                                                 | **Excluded from MVP** |

### 4.10 Data update strategy

Every collection run inserts new `market_snapshots`, `market_metrics`, signals,
and collection logs. Briefing and scenario workers append their own request,
event, block, and final-content rows. Only current market status and last-seen
metadata update in place.

### 4.11 Retention policy

Market, metric, evidence, and briefing rows remain append-only. Scenario
conversation rows expire after 24 hours and are hard-deleted on owner request or
expiry handling. Long-term market-snapshot downsampling is not implemented.

### 4.12 Schema scope summary

The implemented schema covers markets, outcomes, snapshots, metrics, signals,
reports, related material, collection logs, context evidence, resolution rules,
generation requests/events/blocks, and ephemeral scenario state. `users`,
`watchlists`, and wallet/participant-level tables are excluded.

### 4.13 Automated-context extension

Append-only migration `backend/migrations/002_context_candidates.sql` adds:

- `context_candidates`: UUID id, market FK, episode/event timing, neutral
  summary, JSONB citation sources, constrained verification state
  (`verified`/`withheld`/`rejected`), internal verification score, research and
  verifier model IDs, policy version, unique evidence hash, collection timing,
  and expiry timing.
- `context_collection_runs`: UUID id, market FK, episode and run timing,
  constrained status (`success`/`partial`/`failed`/`no_candidate`), query/result/
  accepted counts, JSONB model usage, and secret-free JSONB errors.

Indexes cover market/episode/state lookup. The migration must document FK
delete behavior and duplicate evidence-hash handling. Existing
`related_events`, `ai_reports`, and legacy rows remain unchanged.

### 4.14 On-demand request and lease extension

Migration `004_ai_report_generation_requests.sql` adds:

- `ai_report_generation_requests` is an immutable request identity keyed by
  market and a 64-character SHA-256 input fingerprint. It stores prompt,
  policy, and input-schema versions, request origin, bounded context-refresh
  intent, exact input evidence refs, and request time.
- `ai_report_generation_events` is an append-only event stream. States are
  `queued`, `running`, `succeeded`, and `failed`. Running events require a
  lease token and expiry; success requires an exact `ai_reports` FK; failure
  requires a safe error code. Shape constraints prevent mixed state fields.

The unique market/fingerprint key makes repeated requests join the same
identity. A worker locks the request row, reads the latest event, and appends a
running event only when queued or when the latest running lease has expired.
It then appends exactly one success or failure event. No request/event row is
updated in place. Evidence or prompt revisions create a new fingerprint and
therefore a new immutable request.

### 4.15 Validated-block extension

Append-only migration `005_ai_report_generation_blocks.sql` adds
`ai_report_generation_blocks`. Each row belongs to one immutable generation
request and attempt and stores a unique consecutive sequence number, a
`headline_summary` or `section` type, the already-validated JSON object, and
its recorded time. The table has no update path. A request/attempt/sequence
unique constraint makes replay deterministic, and request deletion cascades
only as part of the existing market/request lifecycle.

### 4.16 Ephemeral scenario-conversation extension

Migration `006_scenario_conversations.sql` adds:

- `scenario_sessions`: issue FK, hashed 256-bit capability, exact definition/
  input fingerprint, policy versions, creation, and fixed 24-hour expiry. It
  stores no raw capability, IP, user agent, or provider content.
- `scenario_turns`: session FK, immutable user/assistant text, unique session
  sequence, hashed idempotency key, and creation time.
- `scenario_premises`: immutable server-owned premise class, normalized text,
  origin turn, and optional evidence refs. No update/promotion operation exists.
- `scenario_generation_requests` and `scenario_generation_events`: immutable
  turn request plus append-only queued/running/succeeded/failed lease events,
  safe errors, and aggregate usage only.
- `scenario_response_blocks`: consecutive already-validated paragraph/list
  objects for authenticated replay.

Composite FKs keep premise origins, user-turn requests, and assistant outcomes
inside the same session. Conversation rows are append-only during the live
session. Expiry or an owner deletion request hard-deletes the entire ephemeral
conversation graph. Only content-free daily aggregates may remain. This privacy
exception does not permit deletion or mutation of issue, metric, evidence,
report, or historical audit rows. Cleanup scheduling and migration application
are deployment responsibilities; new schema changes remain approval-gated.

---
