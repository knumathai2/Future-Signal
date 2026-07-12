-- TASK-126 / ADR-070: ephemeral, capability-scoped scenario conversations.
--
-- Approved for implementation by the user on 2026-07-12. This migration must
-- remain unapplied until a separately approved application step. Provider,
-- infrastructure, deployment, and production actions remain out of scope.

BEGIN;

CREATE TABLE scenario_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets (id) ON DELETE CASCADE,
    capability_hash TEXT NOT NULL UNIQUE,
    definition_ref TEXT NOT NULL,
    input_fingerprint TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    input_schema_version TEXT NOT NULL,
    data_as_of TIMESTAMPTZ NOT NULL,
    caution_note TEXT NOT NULL,
    max_turns INTEGER NOT NULL DEFAULT 8,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_scenario_sessions_capability_hash
        CHECK (capability_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_scenario_sessions_fingerprint
        CHECK (input_fingerprint ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_scenario_sessions_max_turns
        CHECK (max_turns = 8),
    CONSTRAINT ck_scenario_sessions_expiry
        CHECK (expires_at > created_at)
);

CREATE INDEX idx_scenario_sessions_market_created
    ON scenario_sessions (market_id, created_at DESC);
CREATE INDEX idx_scenario_sessions_expiry
    ON scenario_sessions (expires_at);

CREATE TABLE scenario_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL
        REFERENCES scenario_sessions (id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    idempotency_key_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_scenario_turns_sequence
        CHECK (sequence_number >= 1),
    CONSTRAINT ck_scenario_turns_role
        CHECK (role IN ('user', 'assistant')),
    CONSTRAINT ck_scenario_turns_content
        CHECK (
            (role = 'user' AND char_length(content) BETWEEN 1 AND 1000)
            OR
            (role = 'assistant' AND char_length(content) BETWEEN 1 AND 2500)
        ),
    CONSTRAINT ck_scenario_turns_idempotency
        CHECK (
            (role = 'user'
                AND idempotency_key_hash ~ '^[0-9a-f]{64}$')
            OR
            (role = 'assistant' AND idempotency_key_hash IS NULL)
        ),
    CONSTRAINT uq_scenario_turns_session_sequence
        UNIQUE (session_id, sequence_number),
    CONSTRAINT uq_scenario_turns_id_session
        UNIQUE (id, session_id),
    CONSTRAINT uq_scenario_turns_session_idempotency
        UNIQUE (session_id, idempotency_key_hash)
);

CREATE INDEX idx_scenario_turns_session_created
    ON scenario_turns (session_id, created_at, sequence_number);

CREATE TABLE scenario_premises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL
        REFERENCES scenario_sessions (id) ON DELETE CASCADE,
    premise_class TEXT NOT NULL,
    text TEXT NOT NULL,
    origin_turn_id UUID NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_scenario_premises_class
        CHECK (
            premise_class IN (
                'confirmed_fact',
                'stored_observation',
                'user_assumption',
                'model_scenario',
                'unverified_context'
            )
        ),
    CONSTRAINT ck_scenario_premises_text
        CHECK (char_length(text) BETWEEN 1 AND 2000),
    CONSTRAINT ck_scenario_premises_evidence_array
        CHECK (jsonb_typeof(evidence_refs) = 'array'),
    CONSTRAINT fk_scenario_premises_origin_session
        FOREIGN KEY (origin_turn_id, session_id)
        REFERENCES scenario_turns (id, session_id) ON DELETE CASCADE
);

CREATE INDEX idx_scenario_premises_session_created
    ON scenario_premises (session_id, created_at, id);

CREATE TABLE scenario_generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL
        REFERENCES scenario_sessions (id) ON DELETE CASCADE,
    user_turn_id UUID NOT NULL UNIQUE,
    input_fingerprint TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    input_schema_version TEXT NOT NULL,
    input_premise_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    requested_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_scenario_generation_requests_fingerprint
        CHECK (input_fingerprint ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_scenario_generation_requests_premise_array
        CHECK (jsonb_typeof(input_premise_refs) = 'array'),
    CONSTRAINT uq_scenario_generation_requests_id_session
        UNIQUE (id, session_id),
    CONSTRAINT fk_scenario_generation_requests_turn_session
        FOREIGN KEY (user_turn_id, session_id)
        REFERENCES scenario_turns (id, session_id) ON DELETE CASCADE
);

CREATE INDEX idx_scenario_generation_requests_session_requested
    ON scenario_generation_requests (session_id, requested_at DESC, id DESC);

CREATE TABLE scenario_generation_events (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    session_id UUID NOT NULL,
    state TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 0,
    recorded_at TIMESTAMPTZ NOT NULL,
    lease_token UUID,
    lease_expires_at TIMESTAMPTZ,
    assistant_turn_id UUID,
    error_code TEXT,
    usage JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT ck_scenario_generation_events_state
        CHECK (state IN ('queued', 'running', 'succeeded', 'failed')),
    CONSTRAINT ck_scenario_generation_events_attempt
        CHECK (attempt_number >= 0),
    CONSTRAINT ck_scenario_generation_events_usage_object
        CHECK (jsonb_typeof(usage) = 'object'),
    CONSTRAINT ck_scenario_generation_events_shape
        CHECK (
            (state = 'queued'
                AND attempt_number = 0
                AND lease_token IS NULL
                AND lease_expires_at IS NULL
                AND assistant_turn_id IS NULL
                AND error_code IS NULL)
            OR
            (state = 'running'
                AND attempt_number >= 1
                AND lease_token IS NOT NULL
                AND lease_expires_at IS NOT NULL
                AND assistant_turn_id IS NULL
                AND error_code IS NULL)
            OR
            (state = 'succeeded'
                AND attempt_number >= 1
                AND lease_token IS NULL
                AND lease_expires_at IS NULL
                AND assistant_turn_id IS NOT NULL
                AND error_code IS NULL)
            OR
            (state = 'failed'
                AND attempt_number >= 1
                AND lease_token IS NULL
                AND lease_expires_at IS NULL
                AND assistant_turn_id IS NULL
                AND error_code IS NOT NULL)
        ),
    CONSTRAINT fk_scenario_generation_events_request_session
        FOREIGN KEY (request_id, session_id)
        REFERENCES scenario_generation_requests (id, session_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_scenario_generation_events_assistant_session
        FOREIGN KEY (assistant_turn_id, session_id)
        REFERENCES scenario_turns (id, session_id)
);

CREATE INDEX idx_scenario_generation_events_request_recorded
    ON scenario_generation_events (request_id, recorded_at DESC, id DESC);

CREATE TABLE scenario_response_blocks (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL
        REFERENCES scenario_generation_requests (id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    block_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_scenario_response_blocks_nonnegative
        CHECK (attempt_number >= 1 AND sequence_number >= 0),
    CONSTRAINT ck_scenario_response_blocks_type
        CHECK (block_type IN ('paragraph', 'list')),
    CONSTRAINT ck_scenario_response_blocks_payload_object
        CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT uq_scenario_response_blocks_request_attempt_sequence
        UNIQUE (request_id, attempt_number, sequence_number)
);

CREATE INDEX idx_scenario_response_blocks_request_attempt_sequence
    ON scenario_response_blocks (
        request_id,
        attempt_number,
        sequence_number
    );

COMMIT;
