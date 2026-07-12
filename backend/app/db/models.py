"""SQLAlchemy ORM models mirroring the accepted SQL migrations.

The initial schema is used by the DB-backed routes and was applied to the
approved development database. TASK-057 adds v4 context models; its migration
remains local/development-only until a guarded application step is explicitly
run. Production application still requires separate approval.

Append-only rule (Technical Design §4.10): market_snapshots, market_metrics,
issue_signals, ai_reports, context candidates/runs, resolution rules, v8
generation state, and live scenario-conversation rows are insert-only.
Scenario rows alone may be hard-deleted as one ephemeral graph after their
fixed expiry or an authenticated owner deletion request.
Only markets.last_seen_at/status are ever updated in place. Do not add
update/upsert helpers for the append-only tables.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    polymarket_condition_id: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text, index=True)
    outcome_type: Mapped[str] = mapped_column(Text, default="binary")
    status: Mapped[str] = mapped_column(Text, index=True)
    market_created_at: Mapped[datetime | None]
    end_date: Mapped[datetime | None] = mapped_column(index=True)
    first_seen_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]


class MarketOutcome(Base):
    __tablename__ = "market_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id"), index=True
    )
    outcome_label: Mapped[str] = mapped_column(Text)
    token_id: Mapped[str | None] = mapped_column(Text)
    is_tracked: Mapped[bool] = mapped_column(default=False)


class MarketResolutionRule(Base):
    """Append-only source resolution evidence for one market definition."""

    __tablename__ = "market_resolution_rules"
    __table_args__ = (
        UniqueConstraint(
            "market_id",
            "rules_hash",
            name="uq_market_resolution_rules_market_hash",
        ),
        Index(
            "idx_market_resolution_rules_market_collected",
            "market_id",
            "collected_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE")
    )
    condition_text: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exclusions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    resolution_source: Mapped[str | None] = mapped_column(Text)
    source_description_hash: Mapped[str | None] = mapped_column(Text)
    rules_hash: Mapped[str] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MarketSnapshot(Base):
    """Append-only. Never update a row after insert."""

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id"), index=True
    )
    captured_at: Mapped[datetime] = mapped_column(index=True)
    price: Mapped[float] = mapped_column(Numeric(5, 4))
    volume_24h: Mapped[float | None] = mapped_column(Numeric)
    volume_total: Mapped[float | None] = mapped_column(Numeric)
    liquidity: Mapped[float | None] = mapped_column(Numeric)
    best_bid: Mapped[float | None] = mapped_column(Numeric)
    best_ask: Mapped[float | None] = mapped_column(Numeric)


class MarketMetric(Base):
    """Append-only. One row per market per batch run."""

    __tablename__ = "market_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id"), index=True
    )
    computed_at: Mapped[datetime]
    change_24h: Mapped[float | None] = mapped_column(Numeric)
    change_7d: Mapped[float | None] = mapped_column(Numeric)
    volatility_score: Mapped[float | None] = mapped_column(Numeric)
    attention_score: Mapped[float | None] = mapped_column(Numeric)
    heat_score: Mapped[float | None] = mapped_column(Numeric, index=True)
    confidence_level: Mapped[str] = mapped_column(Text)


class IssueSignal(Base):
    """Append-only. Sparse - only rows when a signal fires."""

    __tablename__ = "issue_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id"), index=True
    )
    signal_type: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text)
    window: Mapped[str] = mapped_column(Text)
    magnitude: Mapped[float] = mapped_column(Numeric)
    triggered_at: Mapped[datetime]
    detail: Mapped[dict | None] = mapped_column(JSONB)


class AiReport(Base):
    """Append-only. Failed generations discard - previous report stays live."""

    __tablename__ = "ai_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id"), index=True
    )
    generated_at: Mapped[datetime]
    input_metrics_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("market_metrics.id")
    )
    content: Mapped[dict] = mapped_column(JSONB)
    model_used: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)


class RelatedEvent(Base):
    """Manually curated - 3-5 demo issues only (PRD §8.9)."""

    __tablename__ = "related_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id"), index=True
    )
    event_title: Mapped[str] = mapped_column(Text)
    event_date: Mapped[datetime | None]
    note: Mapped[str] = mapped_column(Text)


class DataCollectionLog(Base):
    __tablename__ = "data_collection_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_started_at: Mapped[datetime]
    run_finished_at: Mapped[datetime | None]
    status: Mapped[str] = mapped_column(Text)
    markets_processed: Mapped[int] = mapped_column(default=0)
    markets_failed: Mapped[int] = mapped_column(default=0)
    error_detail: Mapped[dict | None] = mapped_column(JSONB)


class ContextCandidate(Base):
    """Append-only v4 context candidate with stored citation provenance.

    Duplicate evidence for the same market episode is rejected by the
    ``uq_context_candidates_episode_evidence`` constraint. Callers should
    treat that integrity error as an idempotent skip; existing rows are never
    updated. Deleting a parent market cascades to its candidate audit rows,
    matching the lifecycle rule used by the initial schema.
    """

    __tablename__ = "context_candidates"
    __table_args__ = (
        CheckConstraint(
            "verification_state IN ('verified', 'withheld', 'rejected')",
            name="ck_context_candidates_verification_state",
        ),
        UniqueConstraint(
            "market_id",
            "episode_at",
            "evidence_hash",
            name="uq_context_candidates_episode_evidence",
        ),
        Index(
            "idx_context_candidates_market_episode_state",
            "market_id",
            "episode_at",
            "verification_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE")
    )
    episode_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_title: Mapped[str] = mapped_column(Text)
    event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    neutral_summary: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict]] = mapped_column(JSONB)
    verification_state: Mapped[str] = mapped_column(Text)
    verification_score_internal: Mapped[float | None] = mapped_column(Numeric(6, 5))
    research_model: Mapped[str] = mapped_column(Text)
    verifier_model: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(Text)
    evidence_hash: Mapped[str] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ContextCollectionRun(Base):
    """Append-only audit row for one market's bounded context-research run.

    The JSON fields contain aggregate provider usage and secret-free error
    details only. Parent-market deletion cascades to these operational audit
    rows, matching the candidate and initial-schema lifecycle rule.
    """

    __tablename__ = "context_collection_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'partial', 'failed', 'no_candidate')",
            name="ck_context_collection_runs_status",
        ),
        CheckConstraint(
            "query_count >= 0 AND result_count >= 0 AND accepted_count >= 0",
            name="ck_context_collection_runs_nonnegative_counts",
        ),
        Index(
            "idx_context_collection_runs_market_episode",
            "market_id",
            "episode_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE")
    )
    episode_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    model_usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_detail: Mapped[dict | None] = mapped_column(JSONB)


class AiReportGenerationRequest(Base):
    """Immutable identity and fingerprint for one on-demand v7 request."""

    __tablename__ = "ai_report_generation_requests"
    __table_args__ = (
        CheckConstraint(
            "length(input_fingerprint) = 64 AND input_fingerprint = lower(input_fingerprint)",
            name="ck_ai_report_generation_requests_fingerprint",
        ),
        CheckConstraint(
            "requested_by IN ('user', 'development_evaluation')",
            name="ck_ai_report_generation_requests_requested_by",
        ),
        UniqueConstraint(
            "market_id",
            "input_fingerprint",
            name="uq_ai_report_generation_requests_market_fingerprint",
        ),
        Index(
            "idx_ai_report_generation_requests_market_requested",
            "market_id",
            "requested_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE")
    )
    input_fingerprint: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(Text)
    input_schema_version: Mapped[str] = mapped_column(Text)
    requested_by: Mapped[str] = mapped_column(Text)
    context_refresh_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    input_evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AiReportGenerationEvent(Base):
    """Append-only state, lease, outcome, and usage event for a request."""

    __tablename__ = "ai_report_generation_events"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_ai_report_generation_events_state",
        ),
        CheckConstraint(
            "attempt_number >= 0",
            name="ck_ai_report_generation_events_attempt",
        ),
        CheckConstraint(
            "(state = 'queued' AND lease_token IS NULL AND lease_expires_at IS NULL "
            "AND report_id IS NULL AND error_code IS NULL) OR "
            "(state = 'running' AND attempt_number >= 1 AND lease_token IS NOT NULL "
            "AND lease_expires_at IS NOT NULL AND report_id IS NULL AND error_code IS NULL) OR "
            "(state = 'succeeded' AND attempt_number >= 1 AND lease_token IS NULL "
            "AND lease_expires_at IS NULL AND report_id IS NOT NULL AND error_code IS NULL) OR "
            "(state = 'failed' AND attempt_number >= 1 AND lease_token IS NULL "
            "AND lease_expires_at IS NULL AND report_id IS NULL AND error_code IS NOT NULL)",
            name="ck_ai_report_generation_events_shape",
        ),
        Index(
            "idx_ai_report_generation_events_request_recorded",
            "request_id",
            "recorded_at",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_report_generation_requests.id", ondelete="CASCADE"),
    )
    state: Mapped[str] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_reports.id", ondelete="SET NULL")
    )
    error_code: Mapped[str | None] = mapped_column(Text)
    usage: Mapped[dict] = mapped_column(JSONB, default=dict)


class AiReportGenerationBlock(Base):
    """Append-only, publication-safe writer block for one request attempt."""

    __tablename__ = "ai_report_generation_blocks"
    __table_args__ = (
        CheckConstraint(
            "attempt_number >= 1 AND sequence_number >= 0",
            name="ck_ai_report_generation_blocks_nonnegative",
        ),
        CheckConstraint(
            "block_type IN ('headline_summary', 'section')",
            name="ck_ai_report_generation_blocks_type",
        ),
        UniqueConstraint(
            "request_id",
            "attempt_number",
            "sequence_number",
            name="uq_ai_report_generation_blocks_request_attempt_sequence",
        ),
        Index(
            "idx_ai_report_generation_blocks_request_attempt_sequence",
            "request_id",
            "attempt_number",
            "sequence_number",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_report_generation_requests.id", ondelete="CASCADE"),
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    sequence_number: Mapped[int] = mapped_column(Integer)
    block_type: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioSession(Base):
    """Ephemeral issue-scoped session authorized by a hashed capability."""

    __tablename__ = "scenario_sessions"
    __table_args__ = (
        CheckConstraint(
            "length(capability_hash) = 64 AND capability_hash = lower(capability_hash)",
            name="ck_scenario_sessions_capability_hash",
        ),
        CheckConstraint(
            "length(input_fingerprint) = 64 AND input_fingerprint = lower(input_fingerprint)",
            name="ck_scenario_sessions_fingerprint",
        ),
        CheckConstraint("max_turns = 8", name="ck_scenario_sessions_max_turns"),
        CheckConstraint("expires_at > created_at", name="ck_scenario_sessions_expiry"),
        Index("idx_scenario_sessions_market_created", "market_id", "created_at"),
        Index("idx_scenario_sessions_expiry", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE")
    )
    capability_hash: Mapped[str] = mapped_column(Text, unique=True)
    definition_ref: Mapped[str] = mapped_column(Text)
    input_fingerprint: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(Text)
    input_schema_version: Mapped[str] = mapped_column(Text)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    caution_note: Mapped[str] = mapped_column(Text)
    max_turns: Mapped[int] = mapped_column(Integer, default=8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioTurn(Base):
    """Immutable user or validated-assistant turn within a live session."""

    __tablename__ = "scenario_turns"
    __table_args__ = (
        CheckConstraint("sequence_number >= 1", name="ck_scenario_turns_sequence"),
        CheckConstraint("role IN ('user', 'assistant')", name="ck_scenario_turns_role"),
        CheckConstraint(
            "(role = 'user' AND length(content) BETWEEN 1 AND 1000) OR "
            "(role = 'assistant' AND length(content) BETWEEN 1 AND 2500)",
            name="ck_scenario_turns_content",
        ),
        CheckConstraint(
            "(role = 'user' AND length(idempotency_key_hash) = 64) OR "
            "(role = 'assistant' AND idempotency_key_hash IS NULL)",
            name="ck_scenario_turns_idempotency",
        ),
        UniqueConstraint(
            "session_id", "sequence_number", name="uq_scenario_turns_session_sequence"
        ),
        UniqueConstraint("id", "session_id", name="uq_scenario_turns_id_session"),
        UniqueConstraint(
            "session_id",
            "idempotency_key_hash",
            name="uq_scenario_turns_session_idempotency",
        ),
        Index("idx_scenario_turns_session_created", "session_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_sessions.id", ondelete="CASCADE")
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    idempotency_key_hash: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioPremise(Base):
    """Immutable server-classified premise; no promotion/update path exists."""

    __tablename__ = "scenario_premises"
    __table_args__ = (
        CheckConstraint(
            "premise_class IN ('confirmed_fact', 'stored_observation', "
            "'user_assumption', 'model_scenario', 'unverified_context')",
            name="ck_scenario_premises_class",
        ),
        CheckConstraint(
            "length(text) BETWEEN 1 AND 2000", name="ck_scenario_premises_text"
        ),
        ForeignKeyConstraint(
            ["origin_turn_id", "session_id"],
            ["scenario_turns.id", "scenario_turns.session_id"],
            ondelete="CASCADE",
            name="fk_scenario_premises_origin_session",
        ),
        Index("idx_scenario_premises_session_created", "session_id", "created_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_sessions.id", ondelete="CASCADE")
    )
    premise_class: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    origin_turn_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioGenerationRequest(Base):
    """Immutable request identity for one authenticated scenario user turn."""

    __tablename__ = "scenario_generation_requests"
    __table_args__ = (
        CheckConstraint(
            "length(input_fingerprint) = 64 AND input_fingerprint = lower(input_fingerprint)",
            name="ck_scenario_generation_requests_fingerprint",
        ),
        Index(
            "idx_scenario_generation_requests_session_requested",
            "session_id",
            "requested_at",
            "id",
        ),
        UniqueConstraint(
            "id", "session_id", name="uq_scenario_generation_requests_id_session"
        ),
        ForeignKeyConstraint(
            ["user_turn_id", "session_id"],
            ["scenario_turns.id", "scenario_turns.session_id"],
            ondelete="CASCADE",
            name="fk_scenario_generation_requests_turn_session",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_sessions.id", ondelete="CASCADE")
    )
    user_turn_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    input_fingerprint: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(Text)
    input_schema_version: Mapped[str] = mapped_column(Text)
    input_premise_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioGenerationEvent(Base):
    """Append-only lease/outcome event for a scenario generation request."""

    __tablename__ = "scenario_generation_events"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_scenario_generation_events_state",
        ),
        CheckConstraint("attempt_number >= 0", name="ck_scenario_generation_events_attempt"),
        CheckConstraint(
            "(state = 'queued' AND attempt_number = 0 AND lease_token IS NULL "
            "AND lease_expires_at IS NULL AND assistant_turn_id IS NULL "
            "AND error_code IS NULL) OR "
            "(state = 'running' AND attempt_number >= 1 AND lease_token IS NOT NULL "
            "AND lease_expires_at IS NOT NULL AND assistant_turn_id IS NULL "
            "AND error_code IS NULL) OR "
            "(state = 'succeeded' AND attempt_number >= 1 AND lease_token IS NULL "
            "AND lease_expires_at IS NULL AND assistant_turn_id IS NOT NULL "
            "AND error_code IS NULL) OR "
            "(state = 'failed' AND attempt_number >= 1 AND lease_token IS NULL "
            "AND lease_expires_at IS NULL AND assistant_turn_id IS NULL "
            "AND error_code IS NOT NULL)",
            name="ck_scenario_generation_events_shape",
        ),
        ForeignKeyConstraint(
            ["request_id", "session_id"],
            ["scenario_generation_requests.id", "scenario_generation_requests.session_id"],
            ondelete="CASCADE",
            name="fk_scenario_generation_events_request_session",
        ),
        ForeignKeyConstraint(
            ["assistant_turn_id", "session_id"],
            ["scenario_turns.id", "scenario_turns.session_id"],
            name="fk_scenario_generation_events_assistant_session",
        ),
        Index(
            "idx_scenario_generation_events_request_recorded",
            "request_id",
            "recorded_at",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    state: Mapped[str] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assistant_turn_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    error_code: Mapped[str | None] = mapped_column(Text)
    usage: Mapped[dict] = mapped_column(JSONB, default=dict)


class ScenarioResponseBlock(Base):
    """Append-only complete paragraph/list block safe for replay."""

    __tablename__ = "scenario_response_blocks"
    __table_args__ = (
        CheckConstraint(
            "attempt_number >= 1 AND sequence_number >= 0",
            name="ck_scenario_response_blocks_nonnegative",
        ),
        CheckConstraint(
            "block_type IN ('paragraph', 'list')",
            name="ck_scenario_response_blocks_type",
        ),
        UniqueConstraint(
            "request_id",
            "attempt_number",
            "sequence_number",
            name="uq_scenario_response_blocks_request_attempt_sequence",
        ),
        Index(
            "idx_scenario_response_blocks_request_attempt_sequence",
            "request_id",
            "attempt_number",
            "sequence_number",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenario_generation_requests.id", ondelete="CASCADE"),
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    sequence_number: Mapped[int] = mapped_column(Integer)
    block_type: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
