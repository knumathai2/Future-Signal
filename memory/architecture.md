<!--
Purpose:        System design decisions and architecture structure
Owner:          Backend Implementer (acting Architect)
Update Trigger: New component added, design decision changed, dependency structure changed
Harness Version: 1.1
-->

# Architecture — Outlook Signals

_Last updated: 2026-07-11_
_Full detail: [Technical Design](../docs/tech-design/README.md) — this file is the working summary agents update as the build progresses._

## System Overview

A read-heavy, batch-fed dashboard built to achieve: surface Polymarket-based issue-change signals with strict interpretation-caution safeguards, in 5 days.

**Pattern**: no live trading engine, no synchronous user write path, no message queue/websockets/auth in MVP.

## Component Structure

```
Polymarket public APIs (Gamma + CLOB)
        |  scheduled fetch (GitHub Actions, every 24h)
        v
Batch Collector (Python) -- fetch -> normalize -> snapshot -> metrics -> signals -> verified context -> evidence-grounded reports -> logs
        |  writes
        v
PostgreSQL -- existing tables + approved v4 context_candidates / context_collection_runs
        |  reads only
        v
FastAPI backend (read-only REST API) -- /api/issues /api/issues/:id /api/issues/:id/history /api/issues/:id/report ...
        |  HTTPS/JSON
        v
React + Vite + React Router frontend -- `/` Home / `/issues` Issue List / `/issues/:id` Detail / `/methodology` Disclaimer
```

Key rule: **the API layer never calls the AI provider or Polymarket directly** — it only reads from Postgres. This decouples "is a report fresh" from "is a user waiting," and lets the API degrade to last-known-good data on failure.

## Data Flow

1. Batch collector fetches public Polymarket data for a curated 30–50 market list
2. Normalizes into Pydantic models, validates required fields, quarantines bad records (log + skip, never crash the run)
3. Diffs against the most recent snapshot, inserts a new `market_snapshots` row (append-only)
4. Computes `change_24h`/`change_7d`/`heat_score`/`confidence_level` into `market_metrics`
5. Evaluates the ±5pp threshold for `issue_signals` (cooldown-gated to avoid duplicate firing)
6. Qualifying markets (new expectation-shift row, no report yet, or stale >24h) get a new `ai_reports` row via template-constrained generation plus a safety filter; report prompt inputs use the latest snapshot at or before the metric timestamp so historical-seed metric rows remain usable without fabricating values
7. FastAPI serves the available read-only data; the report endpoint accepts only current `v3` rows whose ADR-033 content and metric-linked timestamp validate, while legacy/failed/malformed rows preserve the neutral empty state
8. React Router renders Home -> Issue List -> Detail -> Chart -> Summary with shareable list query state; detail core, history, and report requests are independent, and the v3 report shows one evidence-first section at a time while keeping report timing plus snapshot caution in the same card
9. TASK-056~065 inserts bounded OpenRouter research after signal detection,
   accepts only API citation annotations, applies deterministic and independent
   verification, stores candidates append-only, and serves only evidence-linked
   v4 reports and verified candidate sources
10. ADR-047 treats deterministic queries as scope anchors and permits only
    unique, bounded provider reformulations with normalized distinctive
    topic/entity overlap. Reported queries are retained in run audit JSON; the
    annotation, source, verifier, publication, and budget gates are unchanged

## Design Decision Summary

> See `decisions.md` for full ADRs

| Decision | Choice | Date |
|----------|--------|------|
| Repo structure | Single monorepo (`/frontend`, `/backend`) | 2026-07-07 |
| Package managers | npm (frontend), pip (backend) | 2026-07-07 |
| CI/CD | GitHub Actions (batch schedule + lint/test) | 2026-07-07 |
| AI generation approach | Template-constrained, LLM only polishes phrasing, banned-phrase filter mandatory | 2026-07-07 (PRD §8.8, Service Design §6) |
| AI report content schema | ADR-033 v3 eight-field report: issue overview, current data reading, nullable external context, reviewed candidate comparison, conditional developments, checks, data limitations, and caution | 2026-07-10 (ADR-033, human-approved public API shape change) |
| AI provider | OpenAI-compatible Chat Completions via `openai==2.44.0`; OpenRouter selected by `OPENROUTER_API_KEY` or `sk-or-` key shape | 2026-07-09 (ADR-022, ADR-027, human-approved) |
| Scheduled report model | GitHub Actions `OPENAI_MODEL` repository variable aligned with the approved project model; workflow keeps its existing fallback only when the variable is absent | 2026-07-10 (ADR-035, human-approved configuration repair) |
| Frontend browser routing | React Router 7 on React 18; `/`, `/issues`, `/issues/:issueId`, and `/methodology`, with scoped Vercel SPA rewrites | 2026-07-10 (ADR-036, human-approved dependency and deployment configuration) |
| Data update strategy | Append-only inserts, no upserts | 2026-07-07 (Technical Design §4.10) |
| Postgres driver | `psycopg[binary]` (psycopg3) | 2026-07-08 (ADR-007, human-approved) |
| Postgres URL compatibility | `psycopg2-binary==2.9.10` for provider-copied `postgresql://...` URLs | 2026-07-09 (ADR-023, human-approved) |
| Migration format (interim) | Plain SQL (`backend/migrations/*.sql`), not Alembic | 2026-07-08 (ADR-007) |
| Automated context v4 | Citation annotations + deterministic hard gates + different verifier model + verified-only public reads; cumulative USD 100, local/dev writes only | 2026-07-11 (ADR-038, human-approved) |
| Server-tool query scope | Deterministic anchors + bounded normalized metadata overlap; exact reported strings audited | 2026-07-11 (ADR-047, human-approved) |

## Architecture Constraints

- Sequential batch script only — no queue/worker infra until report volume or latency demands it (Phase 2)
- API surface uses `issues`/`signals`/`reports`/`categories` naming — never `markets`/`bets`/`trades`/`positions`/`profits` in any public path, including internal code (Technical Design §5)
- No `users`/`watchlists`/wallet-level tables exist even in dormant form — schema itself is a policy signal (Technical Design §4.12)
- `/api/categories` is a read-only broad Korean filter taxonomy derived from currently servable live issue titles/categories when DB data exists; DB-free/failure mode keeps the documented Korean sample fallback. `/api/issues?category=...` accepts those broad Korean labels and raw stored category values. Detailed labels such as `우크라이나 전쟁` and `이란 전쟁` are frontend card-display labels, not top-level filter values.

## Implementation Status (2026-07-10 Day 5 v3 Integrated)

- `/backend` scaffold exists (FastAPI app, `app/api/routes`, `app/core`, `app/db`, `app/schemas`) — see `backend/README.md`. App imports and boots cleanly; smoke-tested via a local venv (`pytest` + a live `uvicorn` request).
- `/frontend` scaffold exists (Vite + React + TS + Tailwind, npm scripts). PR #53 verifies `npm run typecheck`, `npm run lint`, the report-parser regression, and `npm run build` against the TASK-054 route/dashboard baseline. Production build still reports the known Recharts chunk-size warning tracked as TD-001.
- `GET /api/health` is live (mock/no DB dependency).
- `GET /api/issues`, `/api/issues/:id`, and `/api/issues/:id/history` read latest available snapshot/metric/history rows when a database is configured, and otherwise serve the documented static fallback with honest `data_as_of` timestamps (ADR-013). `/api/issues` category filters use the broad Korean taxonomy in `app/core/category_taxonomy.py`, mapping conflict/security topics such as Ukraine or future Iran issues into `세계` while preserving raw source-category compatibility. `/api/issues/:id/history` returns empty `points` when history is unavailable rather than fabricating a latest-point chart. `/api/issues/:id/report` reads the latest successful current-prompt-version `ai_reports` row in live mode and preserves the accepted no-report-yet response when no current successful report exists or the report read fails.
- DB schema draft is accepted (`backend/migrations/001_initial_schema.sql` + `backend/app/db/models.py`) and was applied to the currently configured development Supabase DB on 2026-07-09 after explicit human approval. The configured development DB has been seeded once with 50 normalized issues/snapshots/metrics, so issue list reads can use DB-backed payloads. Applying schema changes to any other shared or production DB remains approval-gated.
- `TASK-007` collector now fetches active Gamma events, validates binary market candidates, writes 50 normalized sample records, and quarantines skipped candidates with structured reasons. Per ADR-014, the artifact emits a display-safe `description: str` and omits raw source descriptions.
- `TASK-008` snapshot/metrics logic computes `change_24h`, `change_7d`, placeholder `heat_score`, and confidence levels through a local/dev-safe path. `TASK-036` adds MVP `caution_low_activity` and `caution_high_volatility` thresholds documented in ADR-019.
- `TASK-009` expectation-shift detector inserts `expectation_shift` rows for the MVP ±5pp threshold with a 24h cooldown and no evaluation for insufficient data.
- `backend/app/core/historical_seed.py` is the guarded local/dev-only path for demo chart history (ADR-025): it appends missing CLOB price-history points, inserts fresh metrics, runs the existing expectation-shift detector, and records a collection log without schema/API changes or rewrites of existing snapshot rows.
- `TASK-054` replaces the dashboard-v1 state flow with real browser routes. Home defaults to 7 days and derives one featured rank-1 issue, a featured-only real-history Recharts preview, a direction summary, a featured-inclusive top-five table, and per-category valid-change arithmetic means from the existing read APIs. `/issues` keeps its 24-hour default plus URL-backed client search/filter/sort/pagination; detail core/history/report reads remain independently cancellable; every route has a main landmark, shared navigation, and direct-entry handling. Scoped Vercel SPA rewrites do not intercept `/api`.
- `TASK-035` verified the existing detail/history read paths for the Day 3 chart/marker flow without changing accepted response shapes.
- `TASK-013` hardened the issue detail chart: 24h/7d/30d windows require baseline-covered history, tooltip values include timestamp/value/previous-point pp change, and markers consume API-provided rows when present.
- `TASK-014` aligned caution badge labels, visual treatment, accessibility labels, and placement across dashboard and detail surfaces.
- `TASK-017` added shared brief caution copy, reusable footer copy, and a dedicated in-app information notice surface without adding a routing dependency.
- `TASK-038` assigned Day 4 active work: `TASK-015` template report generation and safety filter, `TASK-039` report API/fallback readiness, `TASK-016` report display UI, `TASK-019` manual event candidates, `TASK-040` demo/deck draft, and `TASK-018` final wording lint.
- `TASK-049` advances the constrained report pipeline to `PROMPT_VERSION=v3`. Three prose slots are model-authored from structured inputs; candidate comparison, external context, verification items, limitations, and caution are deterministic. Storage is blocked on strict field/length/sentence validation, prohibited wording, metric consistency, public-participant-data scope, conditional later-data scope, reviewed candidate provenance, and exact caution semantics.
- `TASK-039` is now complete via PR #29 follow-up: the report endpoint serves latest successful stored `ai_reports` rows in live mode and keeps the accepted empty state for absent/failed reads.
- `TASK-050` and `TASK-051` implement the v3 report read schema and dynamic UI. The API validates current-version stored content and metric-linked timing; the Frontend parser repeats the frozen bounds/sentence contract and renders the approved Korean labels in evidence-first order, with one visible body and null-only external-context hiding. TASK-053 verified this integration at 320px and 375px.
- `TASK-019` is complete via PR #36 at `6d0eb44`: `backend/app/db/seed_related_events.py` can seed exactly four manually curated related-event candidates for normalized/live-reachable issue IDs, with tests covering wording and schema boundaries.
- `TASK-057` adds `002_context_candidates.sql` and matching ORM models for
  append-only candidate/run storage. Duplicate evidence is unique per market
  episode, verification/run states are constrained, and parent-market deletion
  cascades consistently. TASK-065 applied this migration only to the approved
  development DB; production remains untouched.
- `TASK-058` adds the DB-free OpenRouter research client. It submits the
  `openrouter:web_search` server tool through the existing OpenAI SDK, clamps
  searches/results, and converts only API citation annotations into normalized
  evidence. Candidate URLs must exactly match annotations; model-body URLs are
  ignored. ADR-047 additionally audits unique provider-reported query strings
  and requires normalized market metadata overlap.
- `TASK-059` adds deterministic canonical URL, date, entity, condition,
  official/independent-source, duplicate-content, and wording gates followed by
  one no-web verifier call using a different provider family. A model cannot
  override a failed gate; only verified decisions may flow downstream.
- `TASK-060` connects context after signals and before reports. Targets are
  selected by signal/change/heat/staleness or explicit backfill; each market
  commits independently, no-candidate is normal, verified public output is
  capped at three, and recorded cost plus a pre-call reservation is bounded by
  the approved USD 100 program cap.
- `TASK-061` adds the v4 report writer. The model can fill only the issue
  overview and later-check slots; observed metrics, verified context,
  relationship boundary, limitations, and caution are assembled
  deterministically. Stored envelopes link exactly one metric plus same-episode
  verified candidates, retain legacy rows for audit, and charge writer usage to
  the same cumulative budget before TASK-062 exposes any v4 row.
- `TASK-065` completed a 50-target development backfill: 46 distinct issues
  reached normal completed research, no candidate passed every publication
  gate, and the final DB-recorded program spend was USD 3.00263875. Thirteen
  issues have latest successful v4 reports with zero evidence or safety
  mismatches. Guarded offset and stored-context writer modes avoid repeating
  paid research during local evaluation.
- `TASK-062` makes v4 the only public report version. The read helper loads a
  successful v4 row with its linked metric, latest prior snapshot, and only
  verified candidate rows. The route reconstructs deterministic content and
  checks metric/candidate references, episode/timing, strict stored citation
  fields, and URL/domain consistency before exposing the seven fields plus
  approved source metadata. Every legacy, malformed, or mismatched bundle
  returns the neutral empty state; static fallback never invents evidence.
- `TASK-063` consumes only the strict v4 response. The detail chart receives
  public candidate IDs and maps each event time to the nearest visible stored
  observation, while chart markers and candidate cards retain the same ID and
  link in both directions. The report is one evidence-first change episode;
  the context block is omitted entirely for zero candidates, while timing,
  relationship boundary, limitations, and caution remain visible. Source links
  expose only the approved fields and open with `noopener noreferrer`.
- `TASK-064` adds an executable full-flow fixture from research through public
  API output. Review found that SQLite strips timezone information; v4 report
  inputs now normalize snapshot, episode, candidate-event, and end-date values
  to UTC-aware timestamps before deterministic assembly, matching PostgreSQL
  and the API's independent reconstruction boundary.
- `TASK-065` has applied migration 002 to the approved development DB. The
  guarded batch now supports `--context-max-markets`, retries research once,
  and retains usage from failed billed responses. Bulk execution is stopped:
  OpenRouter's server tool generates/reformulates queries, while ADR-040
  currently requires exact membership in the deterministic suggestion list.
  No read/API/publication gate has been relaxed.
- `TASK-041` is complete: `build_prompt_inputs_for_market()` now selects the latest `market_snapshots` row with `captured_at <= market_metrics.computed_at`, matching the historical-seed `+1 microsecond` metric timestamp without fabricating values. Tests cover prompt-input construction, future-only snapshot rejection, and `run_ai_report_batch` inserting a `status=success` row with a fake `LLMClient`. Local/demo run notes live in `reports/task-041-report-generation-readiness.md`; OpenAI report calls are covered by ADR-022 and the provided-key clarification, while writes to the configured development DB remain separately approval-gated.
- `TASK-042` is complete: `backend/app/core/scheduled_batch.py` is the combined scheduled/manual write path for data collection -> snapshot/metric generation -> expectation-shift signal detection -> AI report generation -> collection logging. It supports `--reports-only` for dev/demo report generation against each market's latest existing metric row. `.github/workflows/daily-batch.yml` runs the combined batch every 24h via GitHub Actions using `DATABASE_URL` and an approved AI provider key.
- `ISS-010` restored the repository Actions secrets/model variable and aligned the three LLM-authored v3 prompt fields with ADR-033's existing bounds and scope checks. Branch run `29073226485` completed with 50 processed rows, no collection failures, and 10 successful v3 reports; the latest 10 stored rows passed structural, wording-safety, and semantic validation.
- Backend local setup should use Python 3.11 on this machine; the default Python 3.9 runtime could not install the pinned `psycopg[binary]==3.2.3` binary package.
- Day 4 is closed from this baseline with `TASK-040`, `TASK-018`, and `TASK-045`
  complete. Day 5 can focus on final screenshots, rehearsal, deployment
  approval handling, and presentation polish. Any shared or production schema
  application, non-project paid external AI call, public API shape change,
  deployment, or infrastructure change remains separately approval-gated.
