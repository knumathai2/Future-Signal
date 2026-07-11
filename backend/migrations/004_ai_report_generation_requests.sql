-- TASK-102 / ADR-051: append-only on-demand briefing requests and events.
--
-- Approved for local/development application under TASK-099 items 1-7.
-- Production application, deployment, and edits to existing migrations remain
-- outside the approved boundary.

BEGIN;

CREATE TABLE ai_report_generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    input_fingerprint TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    input_schema_version TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    context_refresh_requested BOOLEAN NOT NULL DEFAULT FALSE,
    input_evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    requested_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_ai_report_generation_requests_market_fingerprint
        UNIQUE (market_id, input_fingerprint),
    CONSTRAINT ck_ai_report_generation_requests_fingerprint
        CHECK (
            input_fingerprint ~ '^[0-9a-f]{64}$'
        ),
    CONSTRAINT ck_ai_report_generation_requests_requested_by
        CHECK (requested_by IN ('user', 'development_evaluation')),
    CONSTRAINT ck_ai_report_generation_requests_evidence_array
        CHECK (jsonb_typeof(input_evidence_refs) = 'array')
);

CREATE INDEX idx_ai_report_generation_requests_market_requested
    ON ai_report_generation_requests (market_id, requested_at DESC);

CREATE TABLE ai_report_generation_events (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL
        REFERENCES ai_report_generation_requests (id) ON DELETE CASCADE,
    state TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 0,
    recorded_at TIMESTAMPTZ NOT NULL,
    lease_token UUID,
    lease_expires_at TIMESTAMPTZ,
    report_id UUID REFERENCES ai_reports (id) ON DELETE SET NULL,
    error_code TEXT,
    usage JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT ck_ai_report_generation_events_state
        CHECK (state IN ('queued', 'running', 'succeeded', 'failed')),
    CONSTRAINT ck_ai_report_generation_events_attempt
        CHECK (attempt_number >= 0),
    CONSTRAINT ck_ai_report_generation_events_usage_object
        CHECK (jsonb_typeof(usage) = 'object'),
    CONSTRAINT ck_ai_report_generation_events_shape
        CHECK (
            (state = 'queued'
                AND lease_token IS NULL
                AND lease_expires_at IS NULL
                AND report_id IS NULL
                AND error_code IS NULL)
            OR
            (state = 'running'
                AND attempt_number >= 1
                AND lease_token IS NOT NULL
                AND lease_expires_at IS NOT NULL
                AND report_id IS NULL
                AND error_code IS NULL)
            OR
            (state = 'succeeded'
                AND attempt_number >= 1
                AND lease_token IS NULL
                AND lease_expires_at IS NULL
                AND report_id IS NOT NULL
                AND error_code IS NULL)
            OR
            (state = 'failed'
                AND attempt_number >= 1
                AND lease_token IS NULL
                AND lease_expires_at IS NULL
                AND report_id IS NULL
                AND error_code IS NOT NULL)
        )
);

CREATE INDEX idx_ai_report_generation_events_request_recorded
    ON ai_report_generation_events (request_id, recorded_at DESC, id DESC);

COMMIT;
