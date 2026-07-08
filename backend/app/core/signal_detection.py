"""Batch collector step 6: sudden-change (expectation-shift) signal detection.

Scope note (TASK-009): implements exactly Technical Design §8. Reads
`market_metrics` rows already written by TASK-008's `run_snapshot_and_metrics`
and writes `issue_signals`. Step 7 (collection logs) and step 8 (AI report
regeneration trigger) are out of scope here - this module's job ends at
making a fired signal queryable in `issue_signals`, since a new signal is one
of the three conditions Technical Design §9 uses to decide whether a market
qualifies for report regeneration.

MVP scope (Service Design §7, Technical Design §8): a single signal type,
`expectation_shift`, evaluated against `abs(change_24h) >= 5pp` (±5pp per PRD
§8.6), always classified `medium` severity - `attention_spike`,
`unusual_activity`, and the low/high/critical severity tiers are explicitly
Phase 2 and are not implemented here.

No-fabrication rule: markets with `confidence_level = insufficient_data` (or
a null `change_24h`) are skipped for this run, never evaluated against the
threshold - mirrors TASK-008's same rule for `market_metrics`.
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.snapshot_metrics import WINDOW_24H
from app.db.models import IssueSignal, MarketMetric

logger = logging.getLogger(__name__)

# +/-5pp per PRD Section 8.6 / Service Design Section 7. `change_24h` (and
# this threshold) are on the same 0-1 price scale as `market_snapshots.price`
# - a 0.05 raw delta is "5 percentage points" of a 0-1 probability, matching
# how TASK-008 already stores `change_24h`/`heat_score`.
EXPECTATION_SHIFT_THRESHOLD = 0.05

# MVP ships exactly one signal type and one severity tier (Service Design
# Section 7: "Ship only Expectation Shift Detected ... for the hackathon").
SIGNAL_TYPE_EXPECTATION_SHIFT = "expectation_shift"
SIGNAL_SEVERITY_MEDIUM = "medium"
SIGNAL_WINDOW_LABEL = "24h"

# Cooldown period: reuse the same 24h window TASK-008 uses for `change_24h`,
# so a market fires at most one expectation_shift signal per rolling day
# instead of one per batch run (Technical Design Section 8 step 2).
SIGNAL_COOLDOWN = WINDOW_24H


def is_in_cooldown(
    db: Session, market_id: uuid.UUID, signal_type: str, now: datetime
) -> bool:
    """True if `market_id` already has an unresolved `signal_type` signal
    within the cooldown window. The schema has no `resolved` flag, so
    "unresolved" is defined as "fired within the last `SIGNAL_COOLDOWN`" -
    Technical Design Section 8 step 2's cooldown check."""
    cutoff = now - SIGNAL_COOLDOWN
    row = db.execute(
        select(IssueSignal.id)
        .where(
            IssueSignal.market_id == market_id,
            IssueSignal.signal_type == signal_type,
            IssueSignal.triggered_at >= cutoff,
        )
        .limit(1)
    ).first()
    return row is not None


def build_expectation_shift_signal(metric: MarketMetric) -> IssueSignal | None:
    """Pure evaluation of one `market_metrics` row against the +/-5pp
    threshold. Returns `None` (never fabricates a signal) when data is
    insufficient or the threshold isn't met - the cooldown check happens
    separately in `detect_signals_for_run` since it needs DB access."""
    if metric.confidence_level == "insufficient_data" or metric.change_24h is None:
        return None

    change = float(metric.change_24h)
    if abs(change) < EXPECTATION_SHIFT_THRESHOLD:
        return None

    return IssueSignal(
        market_id=metric.market_id,
        signal_type=SIGNAL_TYPE_EXPECTATION_SHIFT,
        severity=SIGNAL_SEVERITY_MEDIUM,
        window=SIGNAL_WINDOW_LABEL,
        magnitude=change,
        triggered_at=metric.computed_at,
        detail={
            "metric_id": metric.id,
            "change_24h": change,
            "threshold": EXPECTATION_SHIFT_THRESHOLD,
        },
    )


def detect_signals_for_run(db: Session, run_timestamp: datetime) -> list[IssueSignal]:
    """Step 6 end to end for one batch run: evaluate every `market_metrics`
    row computed at `run_timestamp` (i.e. the metrics TASK-008 just wrote for
    this run) and insert a signal for each market that crosses the threshold
    and isn't already in cooldown. Each insert commits individually so one
    bad row can't block the rest of the run."""
    metrics = (
        db.execute(select(MarketMetric).where(MarketMetric.computed_at == run_timestamp))
        .scalars()
        .all()
    )

    inserted: list[IssueSignal] = []
    for metric in metrics:
        candidate = build_expectation_shift_signal(metric)
        if candidate is None:
            continue
        if is_in_cooldown(db, metric.market_id, candidate.signal_type, run_timestamp):
            logger.info(
                "Skipping duplicate %s signal for market %s: existing signal within cooldown.",
                candidate.signal_type,
                metric.market_id,
            )
            continue
        db.add(candidate)
        db.commit()
        inserted.append(candidate)

    return inserted


if __name__ == "__main__":
    from sqlalchemy import func

    from app.core.config import settings
    from app.db.session import get_session_factory

    if not settings.database_url:
        raise SystemExit(
            "DATABASE_URL is not set. This script writes to a real database and "
            "requires an approved local/dev Postgres instance per AGENTS.md - "
            "set DATABASE_URL before running. For a DB-free dry run, see "
            "backend/tests/test_signal_detection.py, which exercises the same "
            "logic against an in-memory SQLite database."
        )

    session = get_session_factory()()
    try:
        latest_run = session.execute(
            select(func.max(MarketMetric.computed_at))
        ).scalar_one_or_none()
        if latest_run is None:
            raise SystemExit(
                "No market_metrics rows found - run TASK-008's "
                "snapshot_metrics.py collector first."
            )
        signals = detect_signals_for_run(session, latest_run)
    finally:
        session.close()

    logger.info(
        "Fired %s expectation_shift signal(s) for run at %s.", len(signals), latest_run
    )
