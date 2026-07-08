"""Batch collector steps 3-5: compare-with-previous, store snapshot, calculate metrics.

Scope note (TASK-008): this module implements exactly Technical Design §6 steps
3-5. It reads TASK-007's normalized market dicts (e.g. from
`normalized_samples.json` or `collector.fetch_events()`) and writes
`market_snapshots` / `market_metrics`. Step 6 (signal detection), step 7
(collection logs), and step 8 (AI report trigger) are explicitly out of scope
here and belong to later tasks.

Bootstrap note: TASK-007's normalize step never touches the database (it only
produces normalized dicts/JSON), so nothing upstream has created `markets` /
`market_outcomes` rows yet. Steps 3-5 need a stable `market_id` UUID to write
snapshot/metric rows against, so this module also does a minimal
get-or-create of the `markets` row (by `polymarket_condition_id`) and its
single tracked `market_outcomes` row. This is plumbing to satisfy the
existing schema's foreign keys, not a new feature - see ADR in
`memory/decisions.md`. The only in-place update this module performs is
`markets.last_seen_at`/`status`, the one exception to the append-only rule
(Technical Design §4.10).

No-fabrication rule: `change_24h`/`change_7d` are `None` whenever the
trailing history doesn't reach that far back, and `confidence_level` is set
to `insufficient_data` in that case - never a computed or guessed number.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import DataCollectionLog, Market, MarketMetric, MarketOutcome, MarketSnapshot

logger = logging.getLogger(__name__)

DUPLICATE_RUN_LOOKBACK = timedelta(hours=1)
WINDOW_24H = timedelta(hours=24)
WINDOW_7D = timedelta(days=7)

# Placeholder heat_score composite (Service Design §5: "can start as a simple
# weighted rank of |change_24h| + volume-adjusted, don't need full composite
# v1"). Tune once real batch data is visible - see known-issues.md.
HEAT_SCORE_CHANGE_WEIGHT = 500.0
HEAT_SCORE_VOLUME_DIVISOR = 50.0
HEAT_SCORE_VOLUME_CAP = 30.0
HEAT_SCORE_MAX = 100.0


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def has_unfinished_recent_run(db: Session, now: datetime | None = None) -> bool:
    """Duplicate-run guard: is there a collection run started in the last hour
    that hasn't finished? If so, the caller should skip this run entirely
    rather than build distributed-lock infrastructure (Technical Design §6
    "Duplicate prevention")."""
    reference = now or datetime.now(UTC)
    cutoff = reference - DUPLICATE_RUN_LOOKBACK
    row = db.execute(
        select(DataCollectionLog.id)
        .where(
            DataCollectionLog.run_finished_at.is_(None),
            DataCollectionLog.run_started_at >= cutoff,
        )
        .limit(1)
    ).first()
    return row is not None


def get_or_create_market(db: Session, normalized: dict[str, Any], now: datetime) -> Market:
    condition_id = normalized["polymarket_condition_id"]
    market = db.execute(
        select(Market).where(Market.polymarket_condition_id == condition_id)
    ).scalar_one_or_none()

    if market is None:
        market = Market(
            id=uuid.uuid4(),
            polymarket_condition_id=condition_id,
            title=normalized["title"],
            description=normalized.get("description"),
            category=normalized["category"],
            outcome_type=normalized.get("outcome_type", "binary"),
            status=normalized.get("status", "active"),
            market_created_at=parse_iso_datetime(normalized.get("market_created_at")),
            end_date=parse_iso_datetime(normalized.get("end_date")),
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(market)
        db.flush()
        return market

    market.last_seen_at = now
    market.status = normalized.get("status", market.status)
    db.flush()
    return market


def ensure_tracked_outcome(
    db: Session, market: Market, normalized: dict[str, Any]
) -> MarketOutcome:
    outcome = db.execute(
        select(MarketOutcome).where(
            MarketOutcome.market_id == market.id, MarketOutcome.is_tracked.is_(True)
        )
    ).scalar_one_or_none()
    if outcome is not None:
        return outcome

    outcome = MarketOutcome(
        id=uuid.uuid4(),
        market_id=market.id,
        outcome_label=normalized.get("outcome_label", "Yes"),
        token_id=normalized.get("price_history_token"),
        is_tracked=True,
    )
    db.add(outcome)
    db.flush()
    return outcome


@dataclass
class SnapshotPoint:
    """Plain projection of a market_snapshots row (Core row, not an ORM
    entity) so history stays valid across the session commits that happen
    later in the same run - an ORM `MarketSnapshot` instance would otherwise
    get expired-and-reloaded after commit, and SQLite (used in tests) loses
    timezone info on that round trip, breaking window-boundary comparisons."""

    captured_at: datetime
    price: float
    volume_24h: float | None
    liquidity: float | None


def fetch_history(db: Session, market_id: uuid.UUID) -> list[SnapshotPoint]:
    """All prior snapshots for this market, most recent first."""
    rows = db.execute(
        select(
            MarketSnapshot.captured_at,
            MarketSnapshot.price,
            MarketSnapshot.volume_24h,
            MarketSnapshot.liquidity,
        )
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.captured_at.desc())
    ).all()
    return [
        SnapshotPoint(
            captured_at=row.captured_at,
            price=float(row.price),
            volume_24h=float(row.volume_24h) if row.volume_24h is not None else None,
            liquidity=float(row.liquidity) if row.liquidity is not None else None,
        )
        for row in rows
    ]


@dataclass
class RawDelta:
    """Step 3 output: a quick delta against the immediately-prior snapshot,
    ahead of (and separate from) step 5's window-based change_24h/7d calc."""

    is_new_market: bool
    price_delta: float | None
    volume_24h_delta: float | None
    liquidity_delta: float | None


def compute_raw_delta(normalized: dict[str, Any], previous: SnapshotPoint | None) -> RawDelta:
    if previous is None:
        return RawDelta(
            is_new_market=True, price_delta=None, volume_24h_delta=None, liquidity_delta=None
        )

    current_volume = normalized.get("volume_24h")
    current_liquidity = normalized.get("liquidity")
    volume_delta = (
        current_volume - previous.volume_24h
        if current_volume is not None and previous.volume_24h is not None
        else None
    )
    liquidity_delta = (
        current_liquidity - previous.liquidity
        if current_liquidity is not None and previous.liquidity is not None
        else None
    )
    return RawDelta(
        is_new_market=False,
        price_delta=normalized["current_value"] - previous.price,
        volume_24h_delta=volume_delta,
        liquidity_delta=liquidity_delta,
    )


def build_snapshot(
    market_id: uuid.UUID, normalized: dict[str, Any], captured_at: datetime
) -> MarketSnapshot:
    return MarketSnapshot(
        market_id=market_id,
        captured_at=captured_at,
        price=normalized["current_value"],
        volume_24h=normalized.get("volume_24h"),
        volume_total=normalized.get("volume_total"),
        liquidity=normalized.get("liquidity"),
        best_bid=None,
        best_ask=None,
    )


@dataclass
class BatchWriteResult:
    succeeded: list[Any] = field(default_factory=list)
    failed: list[tuple[uuid.UUID, str]] = field(default_factory=list)


def insert_rows_with_fallback(db: Session, rows: list[Any]) -> BatchWriteResult:
    """Insert `rows` (all `market_snapshots` or all `market_metrics` for one
    run) as a single batched INSERT. On failure, retry the batch once. If it
    still fails, fall back to inserting each row in its own transaction
    (retry once each) so one bad market can't crash the whole run - only
    that market is logged and skipped (Technical Design §6 step 4)."""
    if not rows:
        return BatchWriteResult()

    for attempt in (1, 2):
        db.add_all(rows)
        try:
            db.commit()
            return BatchWriteResult(succeeded=list(rows))
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning("Batched insert attempt %s/2 failed: %s", attempt, exc)

    succeeded: list[Any] = []
    failed: list[tuple[uuid.UUID, str]] = []
    for row in rows:
        for attempt in (1, 2):
            db.add(row)
            try:
                db.commit()
                succeeded.append(row)
                break
            except SQLAlchemyError as exc:
                db.rollback()
                if attempt == 2:
                    logger.error("Insert failed for market %s: %s", row.market_id, exc)
                    failed.append((row.market_id, str(exc)))
    return BatchWriteResult(succeeded=succeeded, failed=failed)


def as_utc_naive(value: datetime) -> datetime:
    """Normalizes to a naive UTC datetime for comparison. A real Postgres
    TIMESTAMPTZ column round-trips as tz-aware; SQLite (used in the local/
    dev-safe test path) drops tzinfo on storage - both always represent a
    UTC instant in this project, so comparisons must normalize first rather
    than assume one convention."""
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def compute_change_for_window(
    current_price: float,
    history: list[SnapshotPoint],
    window: timedelta,
    current_captured_at: datetime,
) -> float | None:
    """`history` must be prior snapshots for one market, any order. Finds the
    snapshot closest to (but not after) `current_captured_at - window` and
    returns the price delta against it, or `None` if no snapshot reaches
    that far back (never fabricate a number for a window with insufficient
    history)."""
    boundary = as_utc_naive(current_captured_at - window)
    candidates = [s for s in history if as_utc_naive(s.captured_at) <= boundary]
    if not candidates:
        return None
    reference = max(candidates, key=lambda s: as_utc_naive(s.captured_at))
    return round(current_price - reference.price, 4)


def compute_confidence_level(change_24h: float | None, change_7d: float | None) -> str:
    """Simplified "market confidence score" (Service Design §5, P0 version):
    `insufficient_data` whenever there isn't enough trailing history to
    compute either MVP change window, `sufficient` otherwise.
    `caution_low_activity` / `caution_high_volatility` are accepted by the
    schema but intentionally not populated yet - see known-issues.md (open
    volume/liquidity floor question, and volatility_score is P1/not computed
    by this task)."""
    if change_24h is None or change_7d is None:
        return "insufficient_data"
    return "sufficient"


def compute_heat_score(change_24h: float | None, volume_24h: float | None) -> float | None:
    """Simplified "issue heat score" (Service Design §5, P0 version): a
    bounded composite of |change_24h| plus a small volume boost. `None`
    whenever `change_24h` is `None` - a heat score is meaningless without a
    change to rank."""
    if change_24h is None:
        return None
    volume_boost = min((volume_24h or 0.0) / HEAT_SCORE_VOLUME_DIVISOR, HEAT_SCORE_VOLUME_CAP)
    score = abs(change_24h) * HEAT_SCORE_CHANGE_WEIGHT + volume_boost
    return round(min(score, HEAT_SCORE_MAX), 1)


def build_metric(
    market_id: uuid.UUID,
    computed_at: datetime,
    current_price: float,
    current_volume_24h: float | None,
    history: list[SnapshotPoint],
) -> MarketMetric:
    change_24h = compute_change_for_window(current_price, history, WINDOW_24H, computed_at)
    change_7d = compute_change_for_window(current_price, history, WINDOW_7D, computed_at)
    return MarketMetric(
        market_id=market_id,
        computed_at=computed_at,
        change_24h=change_24h,
        change_7d=change_7d,
        volatility_score=None,  # P1 stretch goal, not computed by TASK-008
        attention_score=None,  # P1 stretch goal, not computed by TASK-008
        heat_score=compute_heat_score(change_24h, current_volume_24h),
        confidence_level=compute_confidence_level(change_24h, change_7d),
    )


@dataclass
class MarketRunOutcome:
    market_id: uuid.UUID
    polymarket_condition_id: str
    is_new_market: bool
    snapshot_stored: bool
    metric_stored: bool
    change_24h: float | None = None
    change_7d: float | None = None
    confidence_level: str | None = None
    error: str | None = None


@dataclass
class BatchRunResult:
    run_timestamp: datetime
    skipped_duplicate_run: bool = False
    markets: list[MarketRunOutcome] = field(default_factory=list)

    @property
    def markets_processed(self) -> int:
        return sum(1 for m in self.markets if m.snapshot_stored)

    @property
    def markets_failed(self) -> int:
        return sum(1 for m in self.markets if not m.snapshot_stored)


def run_snapshot_and_metrics(
    normalized_markets: list[dict[str, Any]], db: Session
) -> BatchRunResult:
    """Steps 3-5 end to end for one batch run's worth of TASK-007 output."""
    if has_unfinished_recent_run(db):
        logger.warning(
            "Skipping run: an unfinished collection run started within the last hour."
        )
        return BatchRunResult(run_timestamp=datetime.now(UTC), skipped_duplicate_run=True)

    run_timestamp = datetime.now(UTC)
    snapshots: list[MarketSnapshot] = []
    context_by_market_id: dict[uuid.UUID, dict[str, Any]] = {}
    prepare_errors: list[MarketRunOutcome] = []

    for normalized in normalized_markets:
        condition_id = normalized.get("polymarket_condition_id", "unknown")
        try:
            market = get_or_create_market(db, normalized, run_timestamp)
            ensure_tracked_outcome(db, market, normalized)
            market_id = market.id
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Failed to upsert market %s: %s", condition_id, exc)
            prepare_errors.append(
                MarketRunOutcome(
                    market_id=uuid.uuid4(),
                    polymarket_condition_id=condition_id,
                    is_new_market=False,
                    snapshot_stored=False,
                    metric_stored=False,
                    error=str(exc),
                )
            )
            continue

        history = fetch_history(db, market_id)  # step 3 input: previous snapshot(s)
        delta = compute_raw_delta(normalized, history[0] if history else None)

        snapshot = build_snapshot(market_id, normalized, run_timestamp)
        snapshots.append(snapshot)
        context_by_market_id[market_id] = {
            "condition_id": condition_id,
            "history": history,
            "is_new_market": delta.is_new_market,
            "current_value": normalized["current_value"],
            "volume_24h": normalized.get("volume_24h"),
        }

    snapshot_result = insert_rows_with_fallback(db, snapshots)
    snapshot_failures = dict(snapshot_result.failed)

    metrics: list[MarketMetric] = []
    for snapshot in snapshot_result.succeeded:
        ctx = context_by_market_id[snapshot.market_id]
        metrics.append(
            build_metric(
                snapshot.market_id,
                run_timestamp,
                ctx["current_value"],
                ctx["volume_24h"],
                ctx["history"],
            )
        )

    metric_result = insert_rows_with_fallback(db, metrics)
    metric_by_market_id = {metric.market_id: metric for metric in metric_result.succeeded}
    metric_failures = dict(metric_result.failed)

    outcomes: list[MarketRunOutcome] = list(prepare_errors)
    for market_id, ctx in context_by_market_id.items():
        metric = metric_by_market_id.get(market_id)
        change_24h = float(metric.change_24h) if metric and metric.change_24h is not None else None
        change_7d = float(metric.change_7d) if metric and metric.change_7d is not None else None
        outcomes.append(
            MarketRunOutcome(
                market_id=market_id,
                polymarket_condition_id=ctx["condition_id"],
                is_new_market=ctx["is_new_market"],
                snapshot_stored=market_id not in snapshot_failures,
                metric_stored=metric is not None,
                change_24h=change_24h,
                change_7d=change_7d,
                confidence_level=metric.confidence_level if metric else None,
                error=snapshot_failures.get(market_id) or metric_failures.get(market_id),
            )
        )

    return BatchRunResult(run_timestamp=run_timestamp, markets=outcomes)


if __name__ == "__main__":
    import json
    from pathlib import Path

    from app.core.config import settings
    from app.db.session import get_session_factory

    if not settings.database_url:
        raise SystemExit(
            "DATABASE_URL is not set. This script writes to a real database and "
            "requires an approved local/dev Postgres instance per AGENTS.md - "
            "set DATABASE_URL before running. For a DB-free dry run, see "
            "backend/tests/test_snapshot_metrics.py, which exercises the same "
            "pipeline against an in-memory SQLite database."
        )

    normalized_path = Path(__file__).resolve().parents[3] / "normalized_samples.json"
    with normalized_path.open(encoding="utf-8") as fh:
        markets = json.load(fh)

    session = get_session_factory()()
    try:
        result = run_snapshot_and_metrics(markets, session)
    finally:
        session.close()

    if result.skipped_duplicate_run:
        logger.info("Run skipped: an unfinished collection run is already in progress.")
    else:
        logger.info(
            "Processed %s markets (%s failed). New markets this run: %s.",
            result.markets_processed,
            result.markets_failed,
            sum(1 for m in result.markets if m.is_new_market),
        )
