-- TASK-083 / ADR-049: append-only source resolution evidence.
--
-- Approved for code implementation only. This migration is not applied by this
-- task to any local, development, shared, or production database.

BEGIN;

CREATE TABLE market_resolution_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    condition_text TEXT,
    deadline TIMESTAMPTZ,
    exclusions JSONB NOT NULL DEFAULT '[]'::jsonb,
    resolution_source TEXT,
    source_description_hash TEXT,
    rules_hash TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_market_resolution_rules_market_hash
        UNIQUE (market_id, rules_hash),
    CONSTRAINT ck_market_resolution_rules_exclusions_array
        CHECK (jsonb_typeof(exclusions) = 'array')
);

CREATE INDEX idx_market_resolution_rules_market_collected
    ON market_resolution_rules (market_id, collected_at DESC);

COMMIT;
