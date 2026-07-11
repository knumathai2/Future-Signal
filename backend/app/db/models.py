"""SQLAlchemy ORM models mirroring the accepted SQL migrations.

The initial schema is used by the DB-backed routes and was applied to the
approved development database. TASK-057 adds v4 context models; its migration
remains local/development-only until a guarded application step is explicitly
run. Production application still requires separate approval.

Append-only rule (Technical Design §4.10): market_snapshots, market_metrics,
issue_signals, ai_reports, context_candidates, and context_collection_runs are
insert-only from the batch collector.
Only markets.last_seen_at/status are ever updated in place. Do not add
update/upsert helpers for the append-only tables.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
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
