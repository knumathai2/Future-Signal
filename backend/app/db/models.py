"""SQLAlchemy ORM models mirroring migrations/001_initial_schema.sql.

DRAFT: these models are not wired to any route yet and the schema has not
been applied to a database (TASK-002 requires human approval first). This
module exists so the eventual DB-backed routes (after TASK-002 approval)
have models ready rather than needing a second design pass.

Append-only rule (Technical Design §4.10): market_snapshots, market_metrics,
issue_signals, and ai_reports are insert-only from the batch collector.
Only markets.last_seen_at/status are ever updated in place. Do not add
update/upsert helpers for the append-only tables.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Numeric, Text
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
