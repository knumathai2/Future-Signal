-- DRAFT SCHEMA — NOT APPLIED TO ANY DATABASE.
-- Human approval is required before running this against any shared or
-- production database (AGENTS.md "Actions Requiring Human Approval";
-- tasks/active.md TASK-002 Definition of Done).
--
-- Mirrors docs/tech-design/02-database-schema.md §4 exactly. No users/
-- watchlists/wallet-level table exists here, even in dormant form, per
-- §4.12 and Service Design §8.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 4.1 markets
CREATE TABLE markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    polymarket_condition_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    outcome_type TEXT NOT NULL DEFAULT 'binary',
    status TEXT NOT NULL,
    market_created_at TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_markets_category ON markets (category);
CREATE INDEX idx_markets_status ON markets (status);
CREATE INDEX idx_markets_end_date ON markets (end_date);

-- 4.2 market_outcomes
CREATE TABLE market_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    outcome_label TEXT NOT NULL,
    token_id TEXT,
    is_tracked BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_market_outcomes_market_id ON market_outcomes (market_id);

-- 4.3 market_snapshots — append-only, highest write volume.
-- Every batch run INSERTs; never UPDATE/UPSERT a snapshot row (§4.10).
CREATE TABLE market_snapshots (
    id BIGSERIAL PRIMARY KEY,
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    captured_at TIMESTAMPTZ NOT NULL,
    price NUMERIC(5, 4) NOT NULL,
    volume_24h NUMERIC,
    volume_total NUMERIC,
    liquidity NUMERIC,
    best_bid NUMERIC,
    best_ask NUMERIC
);
-- Composite index matches the query pattern for every chart/metric calc.
CREATE INDEX idx_market_snapshots_market_captured
    ON market_snapshots (market_id, captured_at DESC);

-- 4.4 market_metrics — append-only, one row per market per batch run.
CREATE TABLE market_metrics (
    id BIGSERIAL PRIMARY KEY,
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    computed_at TIMESTAMPTZ NOT NULL,
    change_24h NUMERIC,
    change_7d NUMERIC,
    volatility_score NUMERIC,
    attention_score NUMERIC,
    heat_score NUMERIC,
    confidence_level TEXT NOT NULL
);
CREATE INDEX idx_market_metrics_market_computed
    ON market_metrics (market_id, computed_at DESC);
CREATE INDEX idx_market_metrics_heat_score ON market_metrics (heat_score);

-- 4.5 issue_signals — append-only, sparse (only rows when a signal fires).
CREATE TABLE issue_signals (
    id BIGSERIAL PRIMARY KEY,
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    "window" TEXT NOT NULL,
    magnitude NUMERIC NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL,
    detail JSONB
);
CREATE INDEX idx_issue_signals_market_triggered
    ON issue_signals (market_id, triggered_at DESC);

-- 4.6 ai_reports — append-only.
CREATE TABLE ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    input_metrics_id BIGINT REFERENCES market_metrics (id),
    content JSONB NOT NULL,
    model_used TEXT,
    prompt_version TEXT,
    status TEXT NOT NULL
);
CREATE INDEX idx_ai_reports_market_generated
    ON ai_reports (market_id, generated_at DESC);

-- 4.7 related_events — manually curated, 3-5 demo issues (PRD §8.9).
CREATE TABLE related_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    event_title TEXT NOT NULL,
    event_date TIMESTAMPTZ,
    note TEXT NOT NULL
);
CREATE INDEX idx_related_events_market_id ON related_events (market_id);

-- 4.8 data_collection_logs
CREATE TABLE data_collection_logs (
    id BIGSERIAL PRIMARY KEY,
    run_started_at TIMESTAMPTZ NOT NULL,
    run_finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    markets_processed INT NOT NULL DEFAULT 0,
    markets_failed INT NOT NULL DEFAULT 0,
    error_detail JSONB
);

COMMIT;
