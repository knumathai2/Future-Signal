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
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    AiReport,
    ContextCandidate,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketResolutionRule,
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
    reference_24h: MarketSnapshot | None = None
    reference_7d: MarketSnapshot | None = None
    recent_history: list[MarketSnapshot] | None = None
    resolution_rule: MarketResolutionRule | None = None


def _load_reference_snapshot(
    db: Session,
    market_id: uuid.UUID,
    metric_at: datetime,
    window: timedelta,
) -> MarketSnapshot | None:
    return db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == market_id,
            MarketSnapshot.captured_at <= metric_at - window,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _load_recent_history(
    db: Session, market_id: uuid.UUID, metric_at: datetime
) -> list[MarketSnapshot]:
    return list(
        db.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.market_id == market_id,
                MarketSnapshot.captured_at >= metric_at - timedelta(days=7),
                MarketSnapshot.captured_at <= metric_at,
            )
            .order_by(MarketSnapshot.captured_at.asc(), MarketSnapshot.id.asc())
        )
        .scalars()
        .all()
    )


def _latest_row_alias(model, *, partition_by, order_by, name: str):
    ranked = select(
        model,
        func.row_number()
        .over(partition_by=partition_by, order_by=order_by)
        .label("latest_rank"),
    ).subquery(name)
    return aliased(model, ranked), ranked.c.latest_rank


def _live_issue(
    market: Market,
    outcome: MarketOutcome,
    snapshot: MarketSnapshot,
    metric: MarketMetric | None,
) -> LiveIssue:
    return LiveIssue(
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
        heat_score=(float(metric.heat_score) if metric and metric.heat_score is not None else None),
        confidence_level=metric.confidence_level if metric else "insufficient_data",
        updated_at=metric.computed_at if metric else snapshot.captured_at,
    )


def _live_issue_select():
    latest_snapshot, snapshot_rank = _latest_row_alias(
        MarketSnapshot,
        partition_by=MarketSnapshot.market_id,
        order_by=(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc()),
        name="latest_market_snapshots",
    )
    latest_metric, metric_rank = _latest_row_alias(
        MarketMetric,
        partition_by=MarketMetric.market_id,
        order_by=(MarketMetric.computed_at.desc(), MarketMetric.id.desc()),
        name="latest_market_metrics",
    )
    ranked_outcomes = (
        select(
            MarketOutcome,
            func.row_number()
            .over(partition_by=MarketOutcome.market_id, order_by=MarketOutcome.id.asc())
            .label("latest_rank"),
        )
        .where(MarketOutcome.is_tracked.is_(True))
        .subquery("tracked_market_outcomes")
    )
    tracked_outcome = aliased(MarketOutcome, ranked_outcomes)
    outcome_rank = ranked_outcomes.c.latest_rank
    query = (
        select(Market, tracked_outcome, latest_snapshot, latest_metric)
        .join(
            tracked_outcome,
            (tracked_outcome.market_id == Market.id)
            & (outcome_rank == 1),
        )
        .join(
            latest_snapshot,
            (latest_snapshot.market_id == Market.id) & (snapshot_rank == 1),
        )
        .outerjoin(
            latest_metric,
            (latest_metric.market_id == Market.id) & (metric_rank == 1),
        )
    )
    return query, latest_snapshot, latest_metric


def load_live_issue(db: Session, market_id: uuid.UUID) -> LiveIssue | None:
    """Load one servable issue with only its latest snapshot and metric."""
    market = db.get(Market, market_id)
    if market is None:
        return None
    outcome = db.execute(
        select(MarketOutcome)
        .where(
            MarketOutcome.market_id == market_id,
            MarketOutcome.is_tracked.is_(True),
        )
        .order_by(MarketOutcome.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    snapshot = db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if outcome is None or snapshot is None:
        return None
    metric = db.execute(
        select(MarketMetric)
        .where(MarketMetric.market_id == market_id)
        .order_by(MarketMetric.computed_at.desc(), MarketMetric.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return _live_issue(market, outcome, snapshot, metric)


def load_live_issues(
    db: Session,
    *,
    window: str = "24h",
    sort: str = "heat",
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[LiveIssue], datetime] | None:
    """Returns `(issues, data_as_of)` from live tables, or `None` when there
    is nothing real to serve yet (no snapshots at all - e.g. TASK-008 has
    not produced data). Callers must fall back to the documented static
    sample path when this returns `None`, not fabricate a response."""
    data_as_of = db.execute(select(func.max(MarketSnapshot.captured_at))).scalar_one()
    if data_as_of is None:
        return None
    query, latest_snapshot, latest_metric = _live_issue_select()
    if sort == "heat":
        query = query.order_by(
            latest_metric.heat_score.is_(None).asc(),
            latest_metric.heat_score.desc(),
            Market.id.asc(),
        )
    elif sort == "change":
        change = latest_metric.change_24h if window == "24h" else latest_metric.change_7d
        query = query.order_by(change.is_(None).asc(), func.abs(change).desc(), Market.id.asc())
    else:
        query = query.order_by(
            func.coalesce(latest_metric.computed_at, latest_snapshot.captured_at).desc(),
            Market.id.asc(),
        )
    if limit is not None:
        query = query.offset(offset).limit(limit)
    rows = db.execute(query).tuples().all()
    issues = [
        _live_issue(market, outcome, snapshot, metric)
        for market, outcome, snapshot, metric in rows
    ]
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


def load_history_points(
    db: Session,
    market_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> list[MarketSnapshot]:
    return list(
        db.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.market_id == market_id,
                MarketSnapshot.captured_at >= since,
                MarketSnapshot.captured_at <= until,
            )
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
        reference_24h=_load_reference_snapshot(
            db, market_id, metric.computed_at, timedelta(hours=24)
        ),
        reference_7d=_load_reference_snapshot(db, market_id, metric.computed_at, timedelta(days=7)),
        recent_history=_load_recent_history(db, market_id, metric.computed_at),
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
                reference_24h=_load_reference_snapshot(
                    db, market_id, metric.computed_at, timedelta(hours=24)
                ),
                reference_7d=_load_reference_snapshot(
                    db, market_id, metric.computed_at, timedelta(days=7)
                ),
                recent_history=_load_recent_history(db, market_id, metric.computed_at),
            )
        )
    return results


def load_successful_v6_reports(
    db: Session,
    market_id: uuid.UUID,
    *,
    limit: int = 20,
) -> list[LiveV4AiReport]:
    """Load recent v6 rows with exact evidence for last-good reconstruction."""
    rows = (
        db.execute(
            select(AiReport, MarketMetric)
            .join(MarketMetric, AiReport.input_metrics_id == MarketMetric.id)
            .where(
                AiReport.market_id == market_id,
                AiReport.status == "success",
                AiReport.prompt_version == "v6",
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
        resolution_rule = None
        raw_rules = (
            report.content.get("resolution_rules") if isinstance(report.content, dict) else None
        )
        rules_hash = raw_rules.get("rules_hash") if isinstance(raw_rules, dict) else None
        if isinstance(rules_hash, str):
            resolution_rule = db.execute(
                select(MarketResolutionRule).where(
                    MarketResolutionRule.market_id == market_id,
                    MarketResolutionRule.rules_hash == rules_hash,
                )
            ).scalar_one_or_none()
        results.append(
            LiveV4AiReport(
                report=report,
                metric=metric,
                snapshot=snapshot,
                candidates=candidates,
                reference_24h=_load_reference_snapshot(
                    db, market_id, metric.computed_at, timedelta(hours=24)
                ),
                reference_7d=_load_reference_snapshot(
                    db, market_id, metric.computed_at, timedelta(days=7)
                ),
                recent_history=_load_recent_history(db, market_id, metric.computed_at),
                resolution_rule=resolution_rule,
            )
        )
    return results
