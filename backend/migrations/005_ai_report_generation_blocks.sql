-- TASK-117 / ADR-060: append-only validated briefing blocks for SSE delivery.
--
-- Approved for local implementation by the user on 2026-07-11 and subsequently
-- applied only to the configured ENV=local development database. Production
-- application and deployment remain outside the approved boundary.

BEGIN;

CREATE TABLE ai_report_generation_blocks (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL
        REFERENCES ai_report_generation_requests (id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    block_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_ai_report_generation_blocks_nonnegative
        CHECK (attempt_number >= 1 AND sequence_number >= 0),
    CONSTRAINT ck_ai_report_generation_blocks_type
        CHECK (block_type IN ('headline_summary', 'section')),
    CONSTRAINT ck_ai_report_generation_blocks_payload_object
        CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT uq_ai_report_generation_blocks_request_attempt_sequence
        UNIQUE (request_id, attempt_number, sequence_number)
);

CREATE INDEX idx_ai_report_generation_blocks_request_attempt_sequence
    ON ai_report_generation_blocks (
        request_id,
        attempt_number,
        sequence_number
    );

COMMIT;
