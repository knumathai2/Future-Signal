"""TASK-009: batch collector step 6 (expectation-shift signal detection).

Uses an in-memory SQLite database (same "local/dev-safe path" pattern as
tests/test_snapshot_metrics.py) so this suite runs end to end without any
shared/production database - see AGENTS.md's human-approval gate on shared/
prod DB writes.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import BigInteger, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.signal_detection import (
    EXPECTATION_SHIFT_THRESHOLD,
    SIGNAL_SEVERITY_MEDIUM,
    SIGNAL_TYPE_EXPECTATION_SHIFT,
    SIGNAL_WINDOW_LABEL,
    build_expectation_shift_signal,
    detect_signals_for_run,
    is_in_cooldown,
)
from app.db.models import Base, IssueSignal, Market, MarketMetric

NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
    # Alias for SQLite's rowid so BigInteger PKs (market_metrics.id,
    # issue_signals.id) autoincrement the way Postgres BIGSERIAL does -
    # mirrors tests/test_snapshot_metrics.py's same override.
    return "INTEGER"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[Market.__table__, MarketMetric.__table__, IssueSignal.__table__],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_market(db, market_id: uuid.UUID = MARKET_ID) -> None:
    db.add(
        Market(
            id=market_id,
            polymarket_condition_id=f"cond-{market_id}",
            title="Will the test issue resolve Yes?",
            description="Tracks reflected expectation in public prediction-market data.",
            category="politics",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=30),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=30),
            last_seen_at=NOW,
        )
    )
    db.commit()


def _metric(
    market_id: uuid.UUID = MARKET_ID,
    computed_at: datetime = NOW,
    change_24h: float | None = 0.08,
    confidence_level: str = "sufficient",
) -> MarketMetric:
    return MarketMetric(
        market_id=market_id,
        computed_at=computed_at,
        change_24h=change_24h,
        change_7d=None,
        volatility_score=None,
        attention_score=None,
        heat_score=40.0,
        confidence_level=confidence_level,
    )


# --- build_expectation_shift_signal (pure evaluation) -----------------------


def test_below_threshold_does_not_trigger():
    metric = _metric(change_24h=0.04)
    assert build_expectation_shift_signal(metric) is None


def test_at_threshold_triggers():
    metric = _metric(change_24h=EXPECTATION_SHIFT_THRESHOLD)
    signal = build_expectation_shift_signal(metric)

    assert signal is not None
    assert signal.signal_type == SIGNAL_TYPE_EXPECTATION_SHIFT
    assert signal.severity == SIGNAL_SEVERITY_MEDIUM
    assert signal.window == SIGNAL_WINDOW_LABEL
    assert signal.magnitude == EXPECTATION_SHIFT_THRESHOLD
    assert signal.triggered_at == NOW


def test_negative_shift_above_threshold_triggers_with_signed_magnitude():
    metric = _metric(change_24h=-0.07)
    signal = build_expectation_shift_signal(metric)

    assert signal is not None
    assert signal.magnitude == -0.07


def test_insufficient_data_is_never_evaluated():
    metric = _metric(change_24h=0.20, confidence_level="insufficient_data")
    assert build_expectation_shift_signal(metric) is None


def test_null_change_24h_is_never_evaluated():
    metric = _metric(change_24h=None, confidence_level="sufficient")
    assert build_expectation_shift_signal(metric) is None


def test_severity_is_always_medium_for_mvp():
    metric = _metric(change_24h=0.99)
    signal = build_expectation_shift_signal(metric)
    assert signal.severity == "medium"


# --- is_in_cooldown ----------------------------------------------------------


def test_is_in_cooldown_true_when_recent_signal_exists(db):
    _seed_market(db)
    db.add(
        IssueSignal(
            market_id=MARKET_ID,
            signal_type=SIGNAL_TYPE_EXPECTATION_SHIFT,
            severity="medium",
            window="24h",
            magnitude=0.08,
            triggered_at=NOW - timedelta(hours=1),
            detail=None,
        )
    )
    db.commit()

    assert is_in_cooldown(db, MARKET_ID, SIGNAL_TYPE_EXPECTATION_SHIFT, NOW) is True


def test_is_in_cooldown_false_once_window_expires(db):
    _seed_market(db)
    db.add(
        IssueSignal(
            market_id=MARKET_ID,
            signal_type=SIGNAL_TYPE_EXPECTATION_SHIFT,
            severity="medium",
            window="24h",
            magnitude=0.08,
            triggered_at=NOW - timedelta(hours=25),
            detail=None,
        )
    )
    db.commit()

    assert is_in_cooldown(db, MARKET_ID, SIGNAL_TYPE_EXPECTATION_SHIFT, NOW) is False


def test_is_in_cooldown_false_for_a_different_signal_type(db):
    _seed_market(db)
    db.add(
        IssueSignal(
            market_id=MARKET_ID,
            signal_type="attention_spike",  # hypothetical Phase 2 type
            severity="medium",
            window="24h",
            magnitude=0.08,
            triggered_at=NOW - timedelta(hours=1),
            detail=None,
        )
    )
    db.commit()

    assert is_in_cooldown(db, MARKET_ID, SIGNAL_TYPE_EXPECTATION_SHIFT, NOW) is False


# --- detect_signals_for_run (end to end) -------------------------------------


def test_no_signal_below_threshold(db):
    _seed_market(db)
    db.add(_metric(change_24h=0.02))
    db.commit()

    fired = detect_signals_for_run(db, NOW)

    assert fired == []
    assert db.execute(select(IssueSignal)).scalars().all() == []


def test_one_signal_fires_at_or_above_threshold(db):
    _seed_market(db)
    db.add(_metric(change_24h=0.08))
    db.commit()

    fired = detect_signals_for_run(db, NOW)

    assert len(fired) == 1
    stored = db.execute(select(IssueSignal)).scalars().all()
    assert len(stored) == 1
    assert stored[0].market_id == MARKET_ID
    assert float(stored[0].magnitude) == 0.08
    assert stored[0].signal_type == SIGNAL_TYPE_EXPECTATION_SHIFT
    assert stored[0].severity == "medium"


def test_no_duplicate_signal_on_second_run_within_cooldown(db):
    _seed_market(db)
    db.add(_metric(computed_at=NOW, change_24h=0.08))
    db.commit()
    first_run = detect_signals_for_run(db, NOW)
    assert len(first_run) == 1

    later = NOW + timedelta(hours=1)
    db.add(_metric(computed_at=later, change_24h=0.09))
    db.commit()
    second_run = detect_signals_for_run(db, later)

    assert second_run == []
    assert len(db.execute(select(IssueSignal)).scalars().all()) == 1


def test_signal_fires_again_once_cooldown_expires(db):
    _seed_market(db)
    db.add(_metric(computed_at=NOW, change_24h=0.08))
    db.commit()
    detect_signals_for_run(db, NOW)

    after_cooldown = NOW + timedelta(hours=25)
    db.add(_metric(computed_at=after_cooldown, change_24h=0.10))
    db.commit()
    third_run = detect_signals_for_run(db, after_cooldown)

    assert len(third_run) == 1
    assert len(db.execute(select(IssueSignal)).scalars().all()) == 2


def test_only_evaluates_metrics_from_the_given_run_timestamp(db):
    _seed_market(db)
    other_market_id = uuid.uuid4()
    _seed_market(db, market_id=other_market_id)
    db.add(_metric(market_id=MARKET_ID, computed_at=NOW, change_24h=0.08))
    db.add(
        _metric(
            market_id=other_market_id,
            computed_at=NOW - timedelta(hours=6),
            change_24h=0.50,
        )
    )
    db.commit()

    fired = detect_signals_for_run(db, NOW)

    assert len(fired) == 1
    assert fired[0].market_id == MARKET_ID
