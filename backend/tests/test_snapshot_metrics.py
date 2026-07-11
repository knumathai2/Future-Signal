"""TASK-008: batch collector steps 3-5 (compare-with-previous, store
snapshot, calculate metrics).

Uses an in-memory SQLite database (same "local/dev-safe path" pattern as
tests/conftest.py's `db_session` fixture) so this suite runs end to end
without any shared/production database - see AGENTS.md's human-approval
gate on shared/prod DB writes.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import BigInteger, create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.snapshot_metrics import (
    SnapshotPoint,
    as_utc_naive,
    compute_change_for_window,
    compute_confidence_level,
    compute_heat_score,
    compute_raw_delta,
    ensure_resolution_rule,
    ensure_tracked_outcome,
    get_or_create_market,
    has_unfinished_recent_run,
    insert_rows_with_fallback,
    run_snapshot_and_metrics,
)
from app.db.models import (
    Base,
    DataCollectionLog,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketResolutionRule,
    MarketSnapshot,
)

NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=UTC)
NORMALIZED_SAMPLES_PATH = Path(__file__).resolve().parents[2] / "normalized_samples.json"


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
    # Alias for SQLite's rowid so BigInteger PKs (market_snapshots.id,
    # market_metrics.id, data_collection_logs.id) autoincrement the way
    # Postgres BIGSERIAL does - mirrors conftest.py's JSONB/UUID overrides.
    return "INTEGER"


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
        "volume_24h": 500.0,
        "volume_total": 10000.0,
        "liquidity": 2000.0,
        "market_created_at": "2026-01-01T00:00:00Z",
        "end_date": "2026-12-31T00:00:00Z",
        "price_history_token": "token-1",
        "resolution_rules": {
            "condition_text": "The source condition must be met by the deadline.",
            "deadline": "2026-12-31T00:00:00Z",
            "exclusions": [],
            "resolution_source": "https://example.gov/policy/rule",
            "source_description_hash": "description-hash",
            "rules_hash": "rules-hash",
            "collected_at": "2026-07-08T12:00:00Z",
        },
    }
    base.update(overrides)
    return base


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            Market.__table__,
            MarketOutcome.__table__,
            MarketResolutionRule.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            DataCollectionLog.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# --- Pure calculation functions -------------------------------------------------


def test_compute_raw_delta_new_market_is_baseline_only():
    delta = compute_raw_delta(_normalized(), previous=None)

    assert delta.is_new_market is True
    assert delta.price_delta is None
    assert delta.volume_24h_delta is None
    assert delta.liquidity_delta is None


def test_compute_raw_delta_against_previous_snapshot():
    previous = SnapshotPoint(
        captured_at=NOW - timedelta(hours=1), price=0.5, volume_24h=400.0, liquidity=1800.0
    )

    normalized = _normalized(current_value=0.6, volume_24h=500.0, liquidity=2000.0)
    delta = compute_raw_delta(normalized, previous)

    assert delta.is_new_market is False
    assert delta.price_delta == pytest.approx(0.1)
    assert delta.volume_24h_delta == pytest.approx(100.0)
    assert delta.liquidity_delta == pytest.approx(200.0)


def _point(hours_ago: float, price: float) -> SnapshotPoint:
    return SnapshotPoint(
        captured_at=NOW - timedelta(hours=hours_ago), price=price, volume_24h=None, liquidity=None
    )


def test_compute_change_for_window_returns_none_without_enough_history():
    history = [_point(2, 0.5)]

    result = compute_change_for_window(0.6, history, timedelta(hours=24), NOW)

    assert result is None


def test_compute_change_for_window_picks_closest_snapshot_at_or_before_boundary():
    history = [_point(30, 0.4), _point(25, 0.5), _point(10, 0.55)]

    result = compute_change_for_window(0.6, history, timedelta(hours=24), NOW)

    # Closest snapshot at-or-before the 24h boundary is the -25h one, not the
    # -10h one (too recent) or the -30h one (further away than necessary).
    assert result == pytest.approx(0.1)


def test_compute_confidence_level():
    assert compute_confidence_level(None, None, 1000.0, 2000.0) == "insufficient_data"
    assert compute_confidence_level(0.05, None, 1000.0, 2000.0) == "insufficient_data"
    assert compute_confidence_level(None, 0.12, 1000.0, 2000.0) == "insufficient_data"
    assert compute_confidence_level(0.05, 0.12, 1000.0, 2000.0) == "sufficient"

    # Test caution conditions
    assert compute_confidence_level(0.05, 0.12, 400.0, 2000.0) == "caution_low_activity"
    assert compute_confidence_level(0.05, 0.12, 1000.0, 500.0) == "caution_low_activity"
    assert compute_confidence_level(0.16, 0.12, 1000.0, 2000.0) == "caution_high_volatility"


def test_compute_heat_score_none_without_change():
    assert compute_heat_score(None, 500.0) is None


def test_compute_heat_score_is_bounded_and_deterministic():
    score = compute_heat_score(0.082, 429.0)

    assert score == pytest.approx(0.082 * 500.0 + min(429.0 / 50.0, 30.0), abs=0.05)
    assert 0 < score <= 100


def test_compute_heat_score_caps_at_max():
    score = compute_heat_score(0.9, 100_000.0)

    assert score == 100.0


# --- DB-touching helpers ---------------------------------------------------------


def test_get_or_create_market_creates_then_reuses_and_updates(db):
    normalized = _normalized()

    first = get_or_create_market(db, normalized, NOW)
    db.commit()

    second = get_or_create_market(
        db, _normalized(status="closed"), NOW + timedelta(hours=1)
    )
    db.commit()

    assert first.id == second.id
    assert db.query(Market).count() == 1
    assert second.status == "closed"
    assert as_utc_naive(second.last_seen_at) == as_utc_naive(NOW + timedelta(hours=1))


def test_ensure_tracked_outcome_is_created_once(db):
    market = get_or_create_market(db, _normalized(), NOW)
    db.commit()

    ensure_tracked_outcome(db, market, _normalized())
    ensure_tracked_outcome(db, market, _normalized())
    db.commit()

    outcomes = db.query(MarketOutcome).filter(MarketOutcome.market_id == market.id).all()
    assert len(outcomes) == 1
    assert outcomes[0].is_tracked is True


def test_ensure_resolution_rule_is_append_only_and_idempotent(db):
    market = get_or_create_market(db, _normalized(), NOW)
    first = ensure_resolution_rule(db, market, _normalized())
    duplicate = ensure_resolution_rule(db, market, _normalized())
    changed = ensure_resolution_rule(
        db,
        market,
        _normalized(
            resolution_rules={
                **_normalized()["resolution_rules"],
                "condition_text": "A revised source condition.",
                "source_description_hash": "revised-description-hash",
                "rules_hash": "revised-rules-hash",
            }
        ),
    )
    db.commit()

    assert first is not None
    assert duplicate is not None
    assert changed is not None
    assert first.id == duplicate.id
    assert first.id != changed.id
    rows = db.query(MarketResolutionRule).filter_by(market_id=market.id).all()
    assert len(rows) == 2
    assert rows[0].exclusions == []
    assert rows[0].resolution_source == "https://example.gov/policy/rule"


def test_has_unfinished_recent_run(db):
    assert has_unfinished_recent_run(db, now=NOW) is False

    db.add(
        DataCollectionLog(
            run_started_at=NOW - timedelta(minutes=10),
            run_finished_at=None,
            status="running",
        )
    )
    db.commit()
    assert has_unfinished_recent_run(db, now=NOW) is True


def test_has_unfinished_recent_run_ignores_old_or_finished_runs(db):
    db.add_all(
        [
            DataCollectionLog(
                run_started_at=NOW - timedelta(hours=2),
                run_finished_at=None,
                status="running",
            ),
            DataCollectionLog(
                run_started_at=NOW - timedelta(minutes=5),
                run_finished_at=NOW,
                status="success",
            ),
        ]
    )
    db.commit()

    assert has_unfinished_recent_run(db, now=NOW) is False


def test_insert_rows_with_fallback_batches_happy_path(db):
    market_a = get_or_create_market(db, _normalized(polymarket_condition_id="a"), NOW)
    market_b = get_or_create_market(db, _normalized(polymarket_condition_id="b"), NOW)
    db.commit()

    snapshots = [
        MarketSnapshot(market_id=market_a.id, captured_at=NOW, price=0.5),
        MarketSnapshot(market_id=market_b.id, captured_at=NOW, price=0.6),
    ]

    result = insert_rows_with_fallback(db, snapshots)

    assert len(result.succeeded) == 2
    assert result.failed == []
    assert db.query(MarketSnapshot).count() == 2


def test_insert_rows_with_fallback_skips_bad_row_without_losing_the_others(db):
    market_a = get_or_create_market(db, _normalized(polymarket_condition_id="a"), NOW)
    market_b = get_or_create_market(db, _normalized(polymarket_condition_id="b"), NOW)
    market_c = get_or_create_market(db, _normalized(polymarket_condition_id="c"), NOW)
    db.commit()

    snapshots = [
        MarketSnapshot(market_id=market_a.id, captured_at=NOW, price=0.5),
        MarketSnapshot(market_id=market_b.id, captured_at=NOW, price=None),  # violates NOT NULL
        MarketSnapshot(market_id=market_c.id, captured_at=NOW, price=0.7),
    ]

    result = insert_rows_with_fallback(db, snapshots)

    assert len(result.succeeded) == 2
    assert len(result.failed) == 1
    assert result.failed[0][0] == market_b.id
    # The whole run didn't crash and the two good rows are actually persisted.
    assert db.query(MarketSnapshot).count() == 2


# --- Full pipeline (steps 3-5) ----------------------------------------------------


def test_run_snapshot_and_metrics_new_market_is_insufficient_data(db):
    result = run_snapshot_and_metrics([_normalized()], db)

    assert result.skipped_duplicate_run is False
    assert result.markets_processed == 1
    outcome = result.markets[0]
    assert outcome.is_new_market is True
    assert outcome.snapshot_stored is True
    assert outcome.metric_stored is True
    assert outcome.change_24h is None
    assert outcome.change_7d is None
    assert outcome.confidence_level == "insufficient_data"

    metric = db.query(MarketMetric).one()
    assert metric.change_24h is None
    assert metric.heat_score is None
    assert metric.confidence_level == "insufficient_data"


def test_run_snapshot_and_metrics_computes_change_24h_on_second_run(db):
    run_snapshot_and_metrics([_normalized(current_value=0.5)], db)

    # Simulate the first run having happened >24h ago, since both runs would
    # otherwise share (almost) the same captured_at in a fast test.
    old_snapshot = db.query(MarketSnapshot).one()
    old_snapshot.captured_at = datetime.now(UTC) - timedelta(hours=25)
    db.commit()

    result = run_snapshot_and_metrics([_normalized(current_value=0.6)], db)

    assert result.markets_processed == 1
    outcome = result.markets[0]
    assert outcome.is_new_market is False
    assert outcome.change_24h == pytest.approx(0.1)
    assert outcome.change_7d is None
    assert outcome.confidence_level == "insufficient_data"

    metric = db.query(MarketMetric).order_by(MarketMetric.computed_at.desc()).first()
    assert metric.heat_score is not None


def test_run_snapshot_and_metrics_sufficient_only_when_24h_and_7d_exist(db):
    run_snapshot_and_metrics([_normalized(current_value=0.4)], db)

    market = db.query(Market).one()
    seven_day_reference = db.query(MarketSnapshot).one()
    seven_day_reference.captured_at = datetime.now(UTC) - timedelta(days=8)
    db.add(
        MarketSnapshot(
            market_id=market.id,
            captured_at=datetime.now(UTC) - timedelta(hours=25),
            price=0.5,
            volume_24h=450.0,
            volume_total=9000.0,
            liquidity=1800.0,
        )
    )
    db.commit()

    result = run_snapshot_and_metrics([_normalized(current_value=0.6)], db)

    outcome = result.markets[0]
    assert outcome.change_24h == pytest.approx(0.1)
    assert outcome.change_7d == pytest.approx(0.2)
    assert outcome.confidence_level == "sufficient"


def test_run_snapshot_and_metrics_snapshot_fallback_preserves_new_parent_rows(db):
    result = run_snapshot_and_metrics(
        [
            _normalized(polymarket_condition_id="a", current_value=0.5),
            _normalized(polymarket_condition_id="b", current_value=None),
            _normalized(polymarket_condition_id="c", current_value=0.7),
        ],
        db,
    )

    assert result.markets_processed == 2
    assert result.markets_failed == 1

    outcomes = {market.polymarket_condition_id: market for market in result.markets}
    assert outcomes["a"].snapshot_stored is True
    assert outcomes["a"].metric_stored is True
    assert outcomes["b"].snapshot_stored is False
    assert outcomes["b"].metric_stored is False
    assert outcomes["c"].snapshot_stored is True
    assert outcomes["c"].metric_stored is True

    assert db.query(Market).count() == 3
    assert db.query(MarketOutcome).count() == 3
    assert db.query(MarketSnapshot).count() == 2
    assert db.query(MarketMetric).count() == 2


def test_run_snapshot_and_metrics_skips_when_duplicate_run_in_progress(db):
    db.add(
        DataCollectionLog(
            run_started_at=datetime.now(UTC) - timedelta(minutes=5),
            run_finished_at=None,
            status="running",
        )
    )
    db.commit()

    result = run_snapshot_and_metrics([_normalized()], db)

    assert result.skipped_duplicate_run is True
    assert result.markets == []
    assert db.query(Market).count() == 0


def test_run_snapshot_and_metrics_end_to_end_against_real_task_007_output(db):
    with NORMALIZED_SAMPLES_PATH.open(encoding="utf-8") as fh:
        normalized_markets = json.load(fh)
    assert len(normalized_markets) >= 30  # sanity check on the fixture itself

    result = run_snapshot_and_metrics(normalized_markets, db)

    assert result.skipped_duplicate_run is False
    assert result.markets_processed == len(normalized_markets)
    assert result.markets_failed == 0
    # First-ever run for every market: no prior history anywhere, so every
    # market must fall back to insufficient_data rather than a fabricated
    # change value.
    assert all(m.is_new_market for m in result.markets)
    assert all(m.change_24h is None for m in result.markets)
    assert all(m.confidence_level == "insufficient_data" for m in result.markets)

    assert db.query(Market).count() == len(normalized_markets)
    assert db.query(MarketOutcome).count() == len(normalized_markets)
    assert db.query(MarketResolutionRule).count() == 0
    assert db.query(MarketSnapshot).count() == len(normalized_markets)
    assert db.query(MarketMetric).count() == len(normalized_markets)
    assert all(uuid.UUID(str(m.market_id)) for m in result.markets)  # ids are real UUIDs
