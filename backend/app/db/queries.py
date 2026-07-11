"""Read-only query helpers backing the issues/signals/history/report API.

Scope note: only reads the tables TASK-010 needs (markets, market_outcomes,
market_snapshots, market_metrics, issue_signals, related_events) plus the
TASK-039/TASK-062 report read paths against existing `ai_reports` and verified
`context_candidates` rows.

No-fabrication rule: a market only becomes a servable "issue" once it has
both a snapshot (for current_value) and a tracked outcome (for
outcome_label) - if either is missing we exclude the market rather than
invent a value. Missing change/heat metrics are represented as
`None` + `confidence_level="insufficient_data"` instead, per
Technical Design §6 step 5 and AGENTS.md's no-fabrication rule.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AiReport,
    ContextCandidate,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketSnapshot,
    RelatedEvent,
)


@dataclass
class LiveIssue:
    market: Market
    outcome_label: str
    current_value: float
    captured_at: datetime
    change_24h: float | None
    change_7d: float | None
    heat_score: float | None
    confidence_level: str
    # sort=recent only, not part of the public response shape
    updated_at: datetime


@dataclass
class LiveAiReport:
    report: AiReport
    data_as_of: datetime


@dataclass
class LiveV4AiReport:
    report: AiReport
    metric: MarketMetric
    snapshot: MarketSnapshot
    candidates: list[ContextCandidate]


def _latest_per_market(rows: list, market_id_attr: str = "market_id") -> dict:
    """`rows` must already be ordered DESC by their timestamp column.

    Small-scale (30-50 market) hackathon dataset - a Python-side "first
    occurrence wins" pass is simpler and just as correct as a per-market
    window-function query here (Technical Design §6 favors simple SQL over
    building more machinery than the data volume needs).
    """
    latest: dict = {}
    for row in rows:
        key = getattr(row, market_id_attr)
        if key not in latest:
            latest[key] = row
    return latest


def load_live_issues(db: Session) -> tuple[list[LiveIssue], datetime] | None:
    """Returns `(issues, data_as_of)` from live tables, or `None` when there
    is nothing real to serve yet (no snapshots at all - e.g. TASK-008 has
    not produced data). Callers must fall back to the documented static
    sample path when this returns `None`, not fabricate a response."""
    snapshots = (
        db.execute(select(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()))
        .scalars()
        .all()
    )
    if not snapshots:
        return None
    data_as_of = snapshots[0].captured_at
    latest_snapshot_by_market = _latest_per_market(snapshots)

    metrics = (
        db.execute(select(MarketMetric).order_by(MarketMetric.computed_at.desc())).scalars().all()
    )
    latest_metric_by_market = _latest_per_market(metrics)

    tracked_outcomes = (
        db.execute(select(MarketOutcome).where(MarketOutcome.is_tracked.is_(True))).scalars().all()
    )
    tracked_outcome_by_market = {o.market_id: o for o in tracked_outcomes}

    markets = (
        db.execute(select(Market).where(Market.id.in_(latest_snapshot_by_market.keys())))
        .scalars()
        .all()
    )

    issues: list[LiveIssue] = []
    for market in markets:
        snapshot = latest_snapshot_by_market.get(market.id)
        outcome = tracked_outcome_by_market.get(market.id)
        if snapshot is None or outcome is None:
            continue  # incomplete data for this market - exclude, don't fabricate
        metric = latest_metric_by_market.get(market.id)
        issues.append(
            LiveIssue(
                market=market,
                outcome_label=outcome.outcome_label,
                current_value=float(snapshot.price),
                captured_at=snapshot.captured_at,
                change_24h=(
                    float(metric.change_24h) if metric and metric.change_24h is not None else None
                ),
                change_7d=(
                    float(metric.change_7d) if metric and metric.change_7d is not None else None
                ),
                heat_score=(
                    float(metric.heat_score) if metric and metric.heat_score is not None else None
                ),
                confidence_level=metric.confidence_level if metric else "insufficient_data",
                updated_at=metric.computed_at if metric else snapshot.captured_at,
            )
        )
    return issues, data_as_of


def load_signals_for_market(db: Session, market_id: uuid.UUID) -> list[IssueSignal]:
    return list(
        db.execute(
            select(IssueSignal)
            .where(IssueSignal.market_id == market_id)
            .order_by(IssueSignal.triggered_at.desc())
        )
        .scalars()
        .all()
    )


def load_related_events_for_market(db: Session, market_id: uuid.UUID) -> list[RelatedEvent]:
    return list(
        db.execute(select(RelatedEvent).where(RelatedEvent.market_id == market_id)).scalars().all()
    )


def load_history_points(db: Session, market_id: uuid.UUID, since: datetime) -> list[MarketSnapshot]:
    return list(
        db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.market_id == market_id, MarketSnapshot.captured_at >= since)
            .order_by(MarketSnapshot.captured_at.asc())
        )
        .scalars()
        .all()
    )


def _latest_successful_report_row(
    db: Session,
    market_id: uuid.UUID,
    prompt_version: str | None = None,
) -> tuple[AiReport, datetime | None] | None:
    query = (
        select(AiReport, MarketMetric.computed_at)
        .outerjoin(MarketMetric, AiReport.input_metrics_id == MarketMetric.id)
        .where(AiReport.market_id == market_id, AiReport.status == "success")
    )
    if prompt_version is not None:
        query = query.where(AiReport.prompt_version == prompt_version)

    return (
        db.execute(query.order_by(AiReport.generated_at.desc(), AiReport.id.desc()).limit(1))
        .tuples()
        .first()
    )


def load_latest_successful_report(
    db: Session,
    market_id: uuid.UUID,
    preferred_prompt_version: str | None = None,
) -> LiveAiReport | None:
    """Return the latest successful stored report for an issue, if one exists.

    `ai_reports` is append-only. Failed rows are kept for traceability but
    should never be served as the user-visible report; if no successful row is
    available, callers should return the accepted neutral empty state. When a
    prompt version is preferred, only that version is returned; legacy rows are
    intentionally treated as not yet generated by the caller.
    """
    if preferred_prompt_version is not None:
        row = _latest_successful_report_row(db, market_id, preferred_prompt_version)
    else:
        row = _latest_successful_report_row(db, market_id)
    if row is None:
        return None
    report, metric_computed_at = row
    return LiveAiReport(
        report=report,
        data_as_of=metric_computed_at,
    )


def load_latest_successful_v4_report(
    db: Session,
    market_id: uuid.UUID,
) -> LiveV4AiReport | None:
    """Load the latest complete v4 evidence bundle for read-time validation.

    This helper intentionally does not decide whether the bundle is public.
    The route validates the strict stored envelope, metric/episode references,
    verified-only candidate state, and public source schema before returning it.
    """
    row = (
        db.execute(
            select(AiReport, MarketMetric)
            .join(MarketMetric, AiReport.input_metrics_id == MarketMetric.id)
            .where(
                AiReport.market_id == market_id,
                AiReport.status == "success",
                AiReport.prompt_version == "v4",
                MarketMetric.market_id == market_id,
            )
            .order_by(AiReport.generated_at.desc(), AiReport.id.desc())
            .limit(1)
        )
        .tuples()
        .first()
    )
    if row is None:
        return None
    report, metric = row
    snapshot = db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == market_id,
            MarketSnapshot.captured_at <= metric.computed_at,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if snapshot is None:
        return None
    candidates = list(
        db.execute(
            select(ContextCandidate)
            .where(
                ContextCandidate.market_id == market_id,
                ContextCandidate.verification_state == "verified",
            )
            .order_by(ContextCandidate.event_at.asc(), ContextCandidate.id.asc())
        )
        .scalars()
        .all()
    )
    return LiveV4AiReport(
        report=report,
        metric=metric,
        snapshot=snapshot,
        candidates=candidates,
    )


def load_successful_v5_reports(
    db: Session,
    market_id: uuid.UUID,
    *,
    limit: int = 20,
) -> list[LiveV4AiReport]:
    """Load recent v5 rows with their evidence for last-good reconstruction."""
    rows = (
        db.execute(
            select(AiReport, MarketMetric)
            .join(MarketMetric, AiReport.input_metrics_id == MarketMetric.id)
            .where(
                AiReport.market_id == market_id,
                AiReport.status == "success",
                AiReport.prompt_version == "v5",
                MarketMetric.market_id == market_id,
            )
            .order_by(AiReport.generated_at.desc(), AiReport.id.desc())
            .limit(limit)
        )
        .tuples()
        .all()
    )
    results: list[LiveV4AiReport] = []
    for report, metric in rows:
        snapshot = db.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.market_id == market_id,
                MarketSnapshot.captured_at <= metric.computed_at,
            )
            .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if snapshot is None:
            continue
        candidates = list(
            db.execute(
                select(ContextCandidate)
                .where(
                    ContextCandidate.market_id == market_id,
                    ContextCandidate.verification_state == "verified",
                )
                .order_by(ContextCandidate.event_at.asc(), ContextCandidate.id.asc())
            )
            .scalars()
            .all()
        )
        results.append(
            LiveV4AiReport(
                report=report,
                metric=metric,
                snapshot=snapshot,
                candidates=candidates,
            )
        )
    return results
