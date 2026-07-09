"""Local/dev historical seed path for DB-backed demo charts.

This module fills the gap left by a first live collector run: the API can
serve DB-backed issue rows after one snapshot, but the detail chart needs
older price points before 24h/7d windows can render honestly.

Safety boundary:
- local/dev/test environments only, with an explicit CLI confirmation flag
- append-only inserts into `market_snapshots`, `market_metrics`,
  `issue_signals`, and `data_collection_logs`
- no schema changes, no existing snapshot/metric rewrites, no user-facing
  feature expansion
"""

import argparse
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.signal_detection import detect_signals_for_run
from app.core.snapshot_metrics import (
    SnapshotPoint,
    as_utc_naive,
    build_metric,
    ensure_tracked_outcome,
    fetch_history,
    get_or_create_market,
    insert_rows_with_fallback,
)
from app.db.models import DataCollectionLog, MarketSnapshot

logger = logging.getLogger(__name__)

CLOB_PRICES_HISTORY_URL = "https://clob.polymarket.com/prices-history"
DEFAULT_HISTORY_INTERVAL = "1w"
DEFAULT_HISTORY_FIDELITY = 60
ALLOWED_WRITE_ENVS = {"local", "dev", "development", "test"}


@dataclass(frozen=True)
class PriceHistoryPoint:
    captured_at: datetime
    price: float


@dataclass
class HistoricalSeedMarketResult:
    polymarket_condition_id: str
    token_id: str | None
    snapshots_inserted: int = 0
    metric_inserted: bool = False
    signals_inserted: int = 0
    skipped_reason: str | None = None
    error: str | None = None


@dataclass
class HistoricalSeedResult:
    run_started_at: datetime
    run_finished_at: datetime | None = None
    markets: list[HistoricalSeedMarketResult] = field(default_factory=list)

    @property
    def snapshots_inserted(self) -> int:
        return sum(m.snapshots_inserted for m in self.markets)

    @property
    def metrics_inserted(self) -> int:
        return sum(1 for m in self.markets if m.metric_inserted)

    @property
    def signals_inserted(self) -> int:
        return sum(m.signals_inserted for m in self.markets)

    @property
    def markets_processed(self) -> int:
        return sum(1 for m in self.markets if m.snapshots_inserted > 0)

    @property
    def markets_failed(self) -> int:
        return sum(1 for m in self.markets if m.error)

    @property
    def markets_skipped(self) -> int:
        return sum(1 for m in self.markets if m.skipped_reason)


def ensure_local_dev_write_allowed(env: str, confirmed: bool) -> None:
    """Hard guard for the historical seed CLI write path."""
    if not confirmed:
        raise RuntimeError(
            "Refusing to write historical seed rows without "
            "--confirm-local-dev-write."
        )
    if env.lower() not in ALLOWED_WRITE_ENVS:
        raise RuntimeError(
            f"Refusing historical seed writes when ENV={env!r}. Allowed values: "
            f"{', '.join(sorted(ALLOWED_WRITE_ENVS))}."
        )


def parse_clob_history(payload: dict[str, Any]) -> list[PriceHistoryPoint]:
    """Parse CLOB prices-history payloads shaped as `{history: [{t, p}, ...]}`."""
    raw_history = payload.get("history")
    if not isinstance(raw_history, list):
        return []

    points_by_time: dict[datetime, PriceHistoryPoint] = {}
    for raw_point in raw_history:
        if not isinstance(raw_point, dict):
            continue
        timestamp = raw_point.get("t")
        price = raw_point.get("p")
        try:
            captured_at = datetime.fromtimestamp(int(timestamp), UTC)
            parsed_price = float(price)
        except (TypeError, ValueError, OSError, OverflowError):
            continue
        if parsed_price < 0 or parsed_price > 1:
            continue
        points_by_time[captured_at] = PriceHistoryPoint(
            captured_at=captured_at,
            price=round(parsed_price, 4),
        )

    return sorted(points_by_time.values(), key=lambda point: point.captured_at)


def fetch_clob_price_history(
    token_id: str,
    interval: str = DEFAULT_HISTORY_INTERVAL,
    fidelity: int = DEFAULT_HISTORY_FIDELITY,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[PriceHistoryPoint]:
    query = urllib.parse.urlencode(
        {"market": token_id, "interval": interval, "fidelity": fidelity}
    )
    request = urllib.request.Request(
        f"{CLOB_PRICES_HISTORY_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with opener(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return parse_clob_history(payload if isinstance(payload, dict) else {})


def load_normalized_markets(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list of normalized markets.")
    return [item for item in payload if isinstance(item, dict)]


def existing_snapshot_instants(db: Session, market_id: Any) -> set[datetime]:
    rows = db.execute(
        select(MarketSnapshot.captured_at).where(MarketSnapshot.market_id == market_id)
    ).all()
    return {as_utc_naive(row.captured_at) for row in rows}


def build_seed_snapshots(
    market_id: Any,
    normalized: dict[str, Any],
    points: list[PriceHistoryPoint],
    existing_instants: set[datetime],
) -> list[MarketSnapshot]:
    """Build append-only snapshot rows, skipping timestamps already present."""
    if not points:
        return []

    point_instants = {as_utc_naive(point.captured_at) for point in points}
    latest_known_instant = max(existing_instants | point_instants)
    rows: list[MarketSnapshot] = []
    for point in points:
        point_instant = as_utc_naive(point.captured_at)
        if point_instant in existing_instants:
            continue

        is_latest_known_point = point_instant == latest_known_instant
        rows.append(
            MarketSnapshot(
                market_id=market_id,
                captured_at=point.captured_at,
                price=point.price,
                volume_24h=(
                    normalized.get("volume_24h") if is_latest_known_point else None
                ),
                volume_total=(
                    normalized.get("volume_total") if is_latest_known_point else None
                ),
                liquidity=normalized.get("liquidity") if is_latest_known_point else None,
                best_bid=None,
                best_ask=None,
            )
        )
    return rows


def latest_and_prior_history(
    history: list[SnapshotPoint],
) -> tuple[SnapshotPoint, list[SnapshotPoint]]:
    if not history:
        raise ValueError("Cannot compute metrics without at least one snapshot.")
    latest = max(history, key=lambda point: as_utc_naive(point.captured_at))
    prior = [point for point in history if point is not latest]
    return latest, prior


def metric_timestamp_for_seed(latest_snapshot_at: datetime) -> datetime:
    """Keep seeded metrics newer than a first-run metric at the same snapshot time."""
    return latest_snapshot_at + timedelta(microseconds=1)


def record_seed_log(db: Session, result: HistoricalSeedResult) -> None:
    status = "success"
    if result.markets_failed:
        status = "partial" if result.markets_processed else "failed"

    db.add(
        DataCollectionLog(
            run_started_at=result.run_started_at,
            run_finished_at=result.run_finished_at,
            status=f"historical_seed_{status}",
            markets_processed=result.markets_processed,
            markets_failed=result.markets_failed,
            error_detail={
                "snapshots_inserted": result.snapshots_inserted,
                "metrics_inserted": result.metrics_inserted,
                "signals_inserted": result.signals_inserted,
                "markets_skipped": result.markets_skipped,
                "errors": [
                    {
                        "polymarket_condition_id": market.polymarket_condition_id,
                        "error": market.error,
                    }
                    for market in result.markets
                    if market.error
                ],
            },
        )
    )
    db.commit()


def seed_historical_snapshots(
    normalized_markets: list[dict[str, Any]],
    histories_by_token: dict[str, list[PriceHistoryPoint]],
    db: Session,
    *,
    record_log: bool = True,
) -> HistoricalSeedResult:
    """Append CLOB history points and recompute latest metrics for seeded markets."""
    result = HistoricalSeedResult(run_started_at=datetime.now(UTC))

    for normalized in normalized_markets:
        condition_id = str(normalized.get("polymarket_condition_id") or "unknown")
        token_id = normalized.get("price_history_token")
        market_result = HistoricalSeedMarketResult(
            polymarket_condition_id=condition_id,
            token_id=str(token_id) if token_id else None,
        )
        result.markets.append(market_result)

        if not token_id:
            market_result.skipped_reason = "missing price_history_token"
            continue

        points = histories_by_token.get(str(token_id), [])
        if len(points) < 2:
            market_result.skipped_reason = "fewer than two history points"
            continue

        try:
            market = get_or_create_market(db, normalized, result.run_started_at)
            ensure_tracked_outcome(db, market, normalized)
            db.commit()

            existing_instants = existing_snapshot_instants(db, market.id)
            snapshots = build_seed_snapshots(
                market.id,
                normalized,
                points,
                existing_instants,
            )
            if not snapshots:
                market_result.skipped_reason = "all history points already present"
                continue

            snapshot_result = insert_rows_with_fallback(db, snapshots)
            market_result.snapshots_inserted = len(snapshot_result.succeeded)
            if snapshot_result.failed:
                market_result.error = "; ".join(error for _, error in snapshot_result.failed)

            if market_result.snapshots_inserted == 0:
                continue

            history = fetch_history(db, market.id)
            latest, prior = latest_and_prior_history(history)
            metric = build_metric(
                market.id,
                metric_timestamp_for_seed(latest.captured_at),
                latest.price,
                (
                    latest.volume_24h
                    if latest.volume_24h is not None
                    else normalized.get("volume_24h")
                ),
                (
                    latest.liquidity
                    if latest.liquidity is not None
                    else normalized.get("liquidity")
                ),
                prior,
            )
            metric_result = insert_rows_with_fallback(db, [metric])
            market_result.metric_inserted = bool(metric_result.succeeded)
            if metric_result.failed:
                market_result.error = "; ".join(error for _, error in metric_result.failed)

            if market_result.metric_inserted:
                signals = detect_signals_for_run(db, metric.computed_at)
                market_result.signals_inserted = len(
                    [signal for signal in signals if signal.market_id == market.id]
                )
        except Exception as exc:
            db.rollback()
            logger.exception("Historical seed failed for market %s.", condition_id)
            market_result.error = str(exc)

    result.run_finished_at = datetime.now(UTC)
    if record_log:
        record_seed_log(db, result)
    return result


def collect_histories(
    normalized_markets: list[dict[str, Any]],
    *,
    interval: str = DEFAULT_HISTORY_INTERVAL,
    fidelity: int = DEFAULT_HISTORY_FIDELITY,
    max_markets: int | None = None,
) -> dict[str, list[PriceHistoryPoint]]:
    histories: dict[str, list[PriceHistoryPoint]] = {}
    selected_markets = normalized_markets[:max_markets] if max_markets else normalized_markets
    for normalized in selected_markets:
        token_id = normalized.get("price_history_token")
        if not token_id or str(token_id) in histories:
            continue
        try:
            histories[str(token_id)] = fetch_clob_price_history(
                str(token_id),
                interval=interval,
                fidelity=fidelity,
            )
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not fetch CLOB history for token %s: %s", token_id, exc)
            histories[str(token_id)] = []
    return histories


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append local/dev historical CLOB snapshots for DB-backed charts."
    )
    parser.add_argument(
        "--normalized-path",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "normalized_samples.json",
    )
    parser.add_argument("--interval", default=DEFAULT_HISTORY_INTERVAL)
    parser.add_argument("--fidelity", type=int, default=DEFAULT_HISTORY_FIDELITY)
    parser.add_argument("--max-markets", type=int, default=None)
    parser.add_argument(
        "--confirm-local-dev-write",
        action="store_true",
        help="Required before this command writes to the configured local/dev DB.",
    )
    return parser


def main() -> int:
    from app.db.session import get_session_factory

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = build_arg_parser().parse_args()
    ensure_local_dev_write_allowed(settings.env, args.confirm_local_dev_write)
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is not set.")

    normalized_markets = load_normalized_markets(args.normalized_path)
    if args.max_markets:
        normalized_markets = normalized_markets[: args.max_markets]
    histories = collect_histories(
        normalized_markets,
        interval=args.interval,
        fidelity=args.fidelity,
    )

    session = get_session_factory()()
    try:
        result = seed_historical_snapshots(normalized_markets, histories, session)
    finally:
        session.close()

    logger.info(
        "Historical seed complete: %s snapshots, %s metrics, %s signals, %s skipped, %s failed.",
        result.snapshots_inserted,
        result.metrics_inserted,
        result.signals_inserted,
        result.markets_skipped,
        result.markets_failed,
    )
    return 0 if result.markets_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
