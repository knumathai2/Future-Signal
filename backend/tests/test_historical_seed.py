"""Historical seed path for live DB-backed charts.

This suite uses the same in-memory SQLite pattern as the batch collector
tests, so it never writes to a shared database.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.historical_seed import (
    PriceHistoryPoint,
    build_seed_snapshots,
    ensure_local_dev_write_allowed,
    metric_timestamp_for_seed,
    parse_clob_history,
    seed_historical_snapshots,
)
from app.core.snapshot_metrics import as_utc_naive
from app.db.models import (
    Base,
    DataCollectionLog,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketSnapshot,
)

NOW = datetime(2026, 7, 9, 6, 0, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
TOKEN_ID = "token-1"


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
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
        tables=[
            Market.__table__,
            MarketOutcome.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            IssueSignal.__table__,
            DataCollectionLog.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _normalized(**overrides) -> dict:
    base = {
        "polymarket_condition_id": "0xcond-1",
        "title": "Will the test issue resolve Yes?",
        "description": "Tracks reflected expectation in public prediction-market data.",
        "category": "politics",
        "status": "active",
        "outcome_type": "binary",
        "outcome_label": "Yes",
        "current_value": 0.6,
        "volume_24h": 1000.0,
        "volume_total": 10000.0,
        "liquidity": 2500.0,
        "market_created_at": "2026-01-01T00:00:00Z",
        "end_date": "2026-12-31T00:00:00Z",
        "price_history_token": TOKEN_ID,
    }
    base.update(overrides)
    return base


def _history(*points: tuple[datetime, float]) -> list[PriceHistoryPoint]:
    return [
        PriceHistoryPoint(captured_at=captured_at, price=price)
        for captured_at, price in points
    ]


def _seed_existing_current_snapshot(db) -> None:
    db.add(
        Market(
            id=MARKET_ID,
            polymarket_condition_id="0xcond-1",
            title="Will the test issue resolve Yes?",
            description="Tracks reflected expectation in public prediction-market data.",
            category="politics",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=30),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=1),
            last_seen_at=NOW,
        )
    )
    db.add(
        MarketOutcome(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            outcome_label="Yes",
            token_id=TOKEN_ID,
            is_tracked=True,
        )
    )
    db.add(
        MarketSnapshot(
            id=1,
            market_id=MARKET_ID,
            captured_at=NOW,
            price=0.6,
            volume_24h=1000.0,
            volume_total=10000.0,
            liquidity=2500.0,
            best_bid=None,
            best_ask=None,
        )
    )
    db.add(
        MarketMetric(
            id=1,
            market_id=MARKET_ID,
            computed_at=NOW,
            change_24h=None,
            change_7d=None,
            volatility_score=None,
            attention_score=None,
            heat_score=None,
            confidence_level="insufficient_data",
        )
    )
    db.commit()


def test_write_guard_requires_explicit_local_dev_confirmation():
    with pytest.raises(RuntimeError, match="confirm-local-dev-write"):
        ensure_local_dev_write_allowed("local", confirmed=False)

    with pytest.raises(RuntimeError, match="ENV='staging'"):
        ensure_local_dev_write_allowed("staging", confirmed=True)

    ensure_local_dev_write_allowed("dev", confirmed=True)


def test_parse_clob_history_sorts_dedupes_and_ignores_bad_points():
    payload = {
        "history": [
            {"t": int(NOW.timestamp()), "p": 0.6},
            {"t": int((NOW - timedelta(hours=1)).timestamp()), "p": "0.55"},
            {"t": "not-a-time", "p": 0.4},
            {"t": int((NOW - timedelta(hours=2)).timestamp()), "p": 1.4},
            {"t": int(NOW.timestamp()), "p": 0.61},
        ]
    }

    points = parse_clob_history(payload)

    assert [(point.captured_at, point.price) for point in points] == [
        (NOW - timedelta(hours=1), 0.55),
        (NOW, 0.61),
    ]


def test_build_seed_snapshots_skips_existing_timestamps():
    points = _history((NOW - timedelta(days=1), 0.5), (NOW, 0.6))

    snapshots = build_seed_snapshots(
        MARKET_ID,
        _normalized(),
        points,
        existing_instants={NOW.replace(tzinfo=None)},
    )

    assert len(snapshots) == 1
    assert snapshots[0].captured_at == NOW - timedelta(days=1)
    assert snapshots[0].volume_24h is None


def test_seed_recomputes_metric_against_existing_current_snapshot(db):
    _seed_existing_current_snapshot(db)
    histories = {
        TOKEN_ID: _history(
            (NOW - timedelta(days=8), 0.4),
            (NOW - timedelta(hours=25), 0.5),
        )
    }

    result = seed_historical_snapshots([_normalized()], histories, db)

    assert result.snapshots_inserted == 2
    assert result.metrics_inserted == 1
    assert result.signals_inserted == 1
    assert result.markets_failed == 0

    latest_metric = db.query(MarketMetric).order_by(MarketMetric.computed_at.desc()).first()
    assert as_utc_naive(latest_metric.computed_at) == as_utc_naive(
        metric_timestamp_for_seed(NOW)
    )
    assert float(latest_metric.change_24h) == pytest.approx(0.1)
    assert float(latest_metric.change_7d) == pytest.approx(0.2)
    assert latest_metric.confidence_level == "sufficient"

    signal = db.query(IssueSignal).one()
    assert float(signal.magnitude) == pytest.approx(0.1)

    log = db.query(DataCollectionLog).one()
    assert log.status == "historical_seed_success"
    assert log.markets_processed == 1

    old_seed_snapshot = next(
        snapshot
        for snapshot in db.query(MarketSnapshot).all()
        if as_utc_naive(snapshot.captured_at)
        == as_utc_naive(NOW - timedelta(hours=25))
    )
    assert old_seed_snapshot.volume_24h is None


def test_seed_creates_market_when_needed_and_uses_latest_history_point(db):
    histories = {
        TOKEN_ID: _history(
            (NOW - timedelta(days=8), 0.3),
            (NOW - timedelta(hours=25), 0.4),
            (NOW, 0.55),
        )
    }

    result = seed_historical_snapshots([_normalized()], histories, db)

    assert result.snapshots_inserted == 3
    assert db.query(Market).count() == 1
    assert db.query(MarketOutcome).count() == 1

    metric = db.query(MarketMetric).one()
    assert as_utc_naive(metric.computed_at) == as_utc_naive(metric_timestamp_for_seed(NOW))
    assert float(metric.change_24h) == pytest.approx(0.15)
    assert float(metric.change_7d) == pytest.approx(0.25)

    latest_snapshot = db.query(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()).first()
    assert latest_snapshot.volume_24h == pytest.approx(1000.0)


def test_seed_is_idempotent_for_existing_history_points(db):
    histories = {
        TOKEN_ID: _history(
            (NOW - timedelta(days=8), 0.4),
            (NOW - timedelta(hours=25), 0.5),
            (NOW, 0.6),
        )
    }

    first = seed_historical_snapshots([_normalized()], histories, db)
    second = seed_historical_snapshots([_normalized()], histories, db)

    assert first.snapshots_inserted == 3
    assert second.snapshots_inserted == 0
    assert second.metrics_inserted == 0
    assert second.markets_skipped == 1
    assert db.query(MarketSnapshot).count() == 3
    assert db.query(MarketMetric).count() == 1
