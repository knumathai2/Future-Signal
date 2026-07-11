-- TASK-057 / ADR-038: append-only storage for verified automated context.
--
-- Approved for local/development databases only. Deployment or application to
-- a production database requires separate human approval. This migration does
-- not modify 001_initial_schema.sql, related_events, ai_reports, or legacy rows.

BEGIN;

CREATE TABLE context_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    episode_at TIMESTAMPTZ NOT NULL,
    event_title TEXT NOT NULL,
    event_at TIMESTAMPTZ,
    neutral_summary TEXT NOT NULL,
    sources JSONB NOT NULL,
    verification_state TEXT NOT NULL CHECK (
        verification_state IN ('verified', 'withheld', 'rejected')
    ),
    verification_score_internal NUMERIC(6, 5),
    research_model TEXT NOT NULL,
    verifier_model TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_context_candidates_episode_evidence
        UNIQUE (market_id, episode_at, evidence_hash)
);

-- One evidence bundle may support different markets or episodes, but the same
-- market episode is idempotent: duplicate evidence is rejected and callers
-- keep the existing append-only row instead of updating it.
CREATE INDEX idx_context_candidates_market_episode_state
    ON context_candidates (market_id, episode_at DESC, verification_state);

CREATE TABLE context_collection_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    episode_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (
        status IN ('success', 'partial', 'failed', 'no_candidate')
    ),
    query_count INT NOT NULL DEFAULT 0,
    result_count INT NOT NULL DEFAULT 0,
    accepted_count INT NOT NULL DEFAULT 0,
    model_usage JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_detail JSONB,
    CONSTRAINT ck_context_collection_runs_nonnegative_counts CHECK (
        query_count >= 0 AND result_count >= 0 AND accepted_count >= 0
    )
);

CREATE INDEX idx_context_collection_runs_market_episode
    ON context_collection_runs (market_id, episode_at DESC);

-- Context rows are audit history while their parent market exists. Deleting a
-- market deliberately cascades to both tables, consistent with every existing
-- market-owned table in 001_initial_schema.sql.

COMMIT;
