"""Issues/signals/reports routes.

Live-data read path (TASK-010): reads markets / market_snapshots /
market_metrics / issue_signals / related_events through
app.db.session.get_db() (see app/db/queries.py for the query helpers).
Per Technical Design §3 / AGENTS.md, this API layer never writes to the DB
and never calls Polymarket or an AI provider directly - not even after DB
wiring.

FALLBACK NOTE: TASK-007/TASK-008 (the batch collector) had not produced any
market_snapshots/market_metrics rows as of this implementation, and
DATABASE_URL may also be unset entirely in local dev. Whenever there is no
live snapshot data to read, these routes fall back to the static sample
dataset below and log a "FALLBACK:" warning on every request, so this can
never become a silent, permanent substitute for live data - once TASK-008
produces real rows the live path takes over automatically, no code change
needed here. See reports/task-010-core-api-notes.md for detail.

`/api/issues/{id}/report` serves only a latest successful v4 evidence bundle
whose stored metric, episode, verified candidates, and citation sources all
validate. Missing, legacy, failed, malformed, or mismatched bundles preserve
the accepted `not_yet_generated` empty state. Static fallback data does not
fabricate a v4 report.
"""
import logging
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.ai_report import (
    V4ContextSource,
    V4LLMFields,
    V4ReportInputs,
    V4StoredReportPayload,
    V4VerifiedCandidateInput,
    assemble_v4_report_content,
    run_v4_safety_and_semantic_checks,
)
from app.core.category_taxonomy import category_matches
from app.core.config import settings
from app.core.snapshot_metrics import as_utc_naive
from app.db.queries import (
    LiveIssue,
    LiveV4AiReport,
    load_history_points,
    load_latest_successful_v4_report,
    load_live_issues,
    load_related_events_for_market,
    load_signals_for_market,
)
from app.db.session import get_db
from app.schemas.issues import (
    ContextCandidateOut,
    ContextSourceOut,
    HistoryPoint,
    IssueDetail,
    IssueHistoryResponse,
    IssueListResponse,
    IssueReportResponse,
    IssueSummary,
    RelatedEventCandidate,
    ReportNotYetGenerated,
    SignalOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["issues"])

_NOW = datetime(2026, 7, 8, 9, 0, 0, tzinfo=UTC)

# Static fallback only - not real Polymarket data. Served when live
# snapshot/metric data is unavailable; see module FALLBACK NOTE above.
_FALLBACK_ISSUES: dict[str, IssueDetail] = {
    "b3f1c2a4-0000-4000-8000-000000000001": IssueDetail(
        id="b3f1c2a4-0000-4000-8000-000000000001",
        title="Will the proposed climate accord be ratified by December 2026?",
        description=(
            "Tracks reflected expectation on ratification of the "
            "multilateral climate accord."
        ),
        category="environment",
        status="active",
        outcome_label="Yes",
        current_value=0.63,
        change_24h=0.082,
        change_7d=0.11,
        confidence_level="sufficient",
        heat_score=78.4,
        data_as_of=_NOW,
        related_events=[],
        signals=[
            SignalOut(
                signal_type="expectation_shift",
                severity="medium",
                window="24h",
                magnitude=0.082,
                triggered_at=_NOW,
            )
        ],
    ),
    "a71e9d3b-0000-4000-8000-000000000002": IssueDetail(
        id="a71e9d3b-0000-4000-8000-000000000002",
        title="Will the central bank announce a rate change at its next meeting?",
        description="Tracks reflected expectation on the next policy rate decision.",
        category="economy",
        status="active",
        outcome_label="Yes",
        current_value=0.41,
        change_24h=-0.02,
        change_7d=0.05,
        confidence_level="caution_low_activity",
        heat_score=34.1,
        data_as_of=_NOW,
        related_events=[],
        signals=[],
    ),
}


def _get_optional_db() -> Generator[Session | None, None, None]:
    """Delegates to app.db.session.get_db() when a database is configured;
    yields None when DATABASE_URL is unset so routes can degrade to the
    static fallback instead of a hard 500 on every request (see module
    FALLBACK NOTE)."""
    if not settings.database_url:
        yield None
        return
    yield from get_db()


def _window_to_timedelta(window: str) -> timedelta:
    return {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }[window]


def _resolve_live(db: Session | None) -> tuple[list[LiveIssue], datetime] | None:
    """Returns `(live_issues, data_as_of)` from the DB, or `None` if the
    caller should fall back to the static sample dataset."""
    if db is None:
        logger.warning(
            "FALLBACK: DATABASE_URL is not set, serving static sample issue data."
        )
        return None
    try:
        result = load_live_issues(db)
    except SQLAlchemyError:
        logger.warning(
            "FALLBACK: live DB query failed, serving static sample issue data.",
            exc_info=True,
        )
        return None
    if result is None:
        logger.warning(
            "FALLBACK: no live snapshot data yet (TASK-008 pending, or a "
            "fresh local DB), serving static sample issue data."
        )
        return None
    return result


def _issue_summary_from_live(live: LiveIssue) -> IssueSummary:
    return IssueSummary(
        id=str(live.market.id),
        title=live.market.title,
        category=live.market.category,
        current_value=live.current_value,
        change_24h=live.change_24h,
        change_7d=live.change_7d,
        confidence_level=live.confidence_level,
        heat_score=live.heat_score,
    )


def _issue_detail_from_live(db: Session, live: LiveIssue, data_as_of: datetime) -> IssueDetail:
    try:
        signals = load_signals_for_market(db, live.market.id)
    except SQLAlchemyError:
        logger.warning(
            "FALLBACK: live signal query failed, serving issue detail without signals.",
            exc_info=True,
        )
        signals = []

    try:
        related = load_related_events_for_market(db, live.market.id)
    except SQLAlchemyError:
        logger.warning(
            "FALLBACK: live related-event query failed, serving issue detail without "
            "related events.",
            exc_info=True,
        )
        related = []

    return IssueDetail(
        id=str(live.market.id),
        title=live.market.title,
        description=live.market.description or "",
        category=live.market.category,
        status=live.market.status,
        outcome_label=live.outcome_label,
        current_value=live.current_value,
        change_24h=live.change_24h,
        change_7d=live.change_7d,
        confidence_level=live.confidence_level,
        heat_score=live.heat_score,
        data_as_of=data_as_of,
        related_events=[
            RelatedEventCandidate(
                event_title=r.event_title,
                event_date=r.event_date,
                note=r.note,
            )
            for r in related
            if r.event_date is not None  # no-fabrication: skip undated candidates
        ],
        signals=[
            SignalOut(
                signal_type=s.signal_type,
                severity=s.severity,
                window=s.window,
                magnitude=float(s.magnitude),
                triggered_at=s.triggered_at,
            )
            for s in signals
        ],
    )


def _find_live(live_issues: list[LiveIssue], issue_id: str) -> LiveIssue | None:
    return next((li for li in live_issues if str(li.market.id) == issue_id), None)


def _same_timestamp(left: datetime, right: datetime) -> bool:
    return as_utc_naive(left) == as_utc_naive(right)


def _not_after(left: datetime, right: datetime) -> bool:
    return as_utc_naive(left) <= as_utc_naive(right)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _issue_report_from_live(
    live_report: LiveV4AiReport,
    live_issue: LiveIssue,
) -> IssueReportResponse:
    report = live_report.report
    metric = live_report.metric
    snapshot = live_report.snapshot
    payload = V4StoredReportPayload.model_validate(report.content)

    if report.input_metrics_id != metric.id or metric.market_id != live_issue.market.id:
        raise ValueError("V4 report metric does not belong to the requested issue")
    if not _not_after(snapshot.captured_at, report.generated_at):
        raise ValueError("V4 report data timestamp is later than generation")
    if not _not_after(payload.episode_at, report.generated_at):
        raise ValueError("V4 report episode is later than generation")
    if len(payload.context_candidate_ids) != len(set(payload.context_candidate_ids)):
        raise ValueError("V4 candidate IDs must be unique")

    candidate_by_id = {candidate.id: candidate for candidate in live_report.candidates}
    candidate_inputs: list[V4VerifiedCandidateInput] = []
    candidate_outputs: list[ContextCandidateOut] = []
    for candidate_id in payload.context_candidate_ids:
        candidate = candidate_by_id.get(candidate_id)
        if (
            candidate is None
            or candidate.verification_state != "verified"
            or candidate.event_at is None
            or not _same_timestamp(candidate.episode_at, payload.episode_at)
            or not candidate.sources
        ):
            raise ValueError("V4 candidate evidence is missing or not public")
        sources = [V4ContextSource.model_validate(source) for source in candidate.sources]
        candidate_inputs.append(
            V4VerifiedCandidateInput(
                id=candidate.id,
                title=candidate.event_title,
                event_at=_as_utc(candidate.event_at),
                neutral_summary=candidate.neutral_summary,
                sources=sources,
            )
        )
        candidate_outputs.append(
            ContextCandidateOut(
                id=str(candidate.id),
                title=candidate.event_title,
                event_at=_as_utc(candidate.event_at),
                summary=candidate.neutral_summary,
                sources=[
                    ContextSourceOut(
                        title=source.title,
                        url=source.url,
                        domain=source.domain,
                        published_at=None,
                        source_type=source.source_type,
                    )
                    for source in sources
                ],
            )
        )

    inputs = V4ReportInputs(
        market_id=live_issue.market.id,
        metric_id=metric.id,
        episode_at=payload.episode_at,
        data_as_of=_as_utc(snapshot.captured_at),
        title=live_issue.market.title,
        description=live_issue.market.description or live_issue.market.title,
        category=live_issue.market.category,
        outcome_label=live_issue.outcome_label,
        end_date=(
            _as_utc(live_issue.market.end_date)
            if live_issue.market.end_date is not None
            else None
        ),
        current_value=float(snapshot.price),
        change_24h=float(metric.change_24h) if metric.change_24h is not None else None,
        change_7d=float(metric.change_7d) if metric.change_7d is not None else None,
        confidence_level=metric.confidence_level,
        volume_24h=float(snapshot.volume_24h) if snapshot.volume_24h is not None else None,
        liquidity=float(snapshot.liquidity) if snapshot.liquidity is not None else None,
        context_candidates=candidate_inputs,
    )
    llm_fields = V4LLMFields(
        issue_overview=payload.content.issue_overview,
        what_to_check=payload.content.what_to_check,
    )
    expected_content = assemble_v4_report_content(inputs, llm_fields)
    validation = run_v4_safety_and_semantic_checks(payload, inputs, llm_fields)
    if expected_content != payload.content:
        expected_fields = expected_content.model_dump() if expected_content else {}
        mismatched_fields = [
            field
            for field, stored_value in payload.content.model_dump().items()
            if expected_fields.get(field) != stored_value
        ]
        raise ValueError(
            "V4 deterministic content does not match stored evidence: "
            + ",".join(mismatched_fields)
        )
    if not validation.passed:
        raise ValueError(f"V4 semantic check failed: {validation.rule}")

    return IssueReportResponse(
        id=str(report.id),
        generated_at=_as_utc(report.generated_at),
        data_as_of=_as_utc(snapshot.captured_at),
        episode_at=_as_utc(payload.episode_at),
        status="success",
        report_version="v4",
        content=payload.content.model_dump(),
        evidence_refs=payload.evidence_refs,
        context_candidates=candidate_outputs,
    )


@router.get("/api/issues", response_model=IssueListResponse)
def list_issues(
    category: str | None = Query(default=None),
    window: str = Query(default="24h", pattern="^(24h|7d)$"),
    sort: str = Query(default="heat", pattern="^(heat|change|recent)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session | None = Depends(_get_optional_db),
) -> IssueListResponse:
    live = _resolve_live(db)
    if live is not None:
        live_issues, data_as_of = live
        if category:
            live_issues = [
                li
                for li in live_issues
                if category_matches(li.market.title, li.market.category, category)
            ]

        def _sort_key(li: LiveIssue):
            if sort == "heat":
                return (li.heat_score is None, -(li.heat_score or 0.0))
            if sort == "change":
                change = li.change_24h if window == "24h" else li.change_7d
                return (change is None, -abs(change or 0.0))
            return (0, -li.updated_at.timestamp())  # sort == "recent"

        live_issues = sorted(live_issues, key=_sort_key)
        page = live_issues[offset : offset + limit]
        return IssueListResponse(
            data_as_of=data_as_of,
            issues=[_issue_summary_from_live(li) for li in page],
        )

    issues = list(_FALLBACK_ISSUES.values())
    if category:
        issues = [i for i in issues if category_matches(i.title, i.category, category)]
    issues = issues[offset : offset + limit]
    return IssueListResponse(
        data_as_of=_NOW,
        issues=[
            IssueSummary(
                id=i.id,
                title=i.title,
                category=i.category,
                current_value=i.current_value,
                change_24h=i.change_24h,
                change_7d=i.change_7d,
                confidence_level=i.confidence_level,
                heat_score=i.heat_score,
            )
            for i in issues
        ],
    )


@router.get("/api/issues/{issue_id}", response_model=IssueDetail)
def get_issue(issue_id: str, db: Session | None = Depends(_get_optional_db)) -> IssueDetail:
    live = _resolve_live(db)
    if live is not None:
        live_issues, data_as_of = live
        match = _find_live(live_issues, issue_id)
        if match is None:
            raise HTTPException(status_code=404, detail="Unknown issue id.")
        return _issue_detail_from_live(db, match, data_as_of)

    issue = _FALLBACK_ISSUES.get(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    return issue


@router.get("/api/issues/{issue_id}/history", response_model=IssueHistoryResponse)
def get_issue_history(
    issue_id: str,
    window: str = Query(default="24h", pattern="^(24h|7d|30d)$"),
    db: Session | None = Depends(_get_optional_db),
) -> IssueHistoryResponse:
    live = _resolve_live(db)
    if live is not None:
        live_issues, data_as_of = live
        match = _find_live(live_issues, issue_id)
        if match is None:
            raise HTTPException(status_code=404, detail="Unknown issue id.")
        since = data_as_of - _window_to_timedelta(window)
        try:
            points = load_history_points(db, match.market.id, since)
        except SQLAlchemyError:
            logger.warning(
                "FALLBACK: live history query failed, returning empty history.",
                exc_info=True,
            )
            points = []
        history_points = [
            HistoryPoint(captured_at=p.captured_at, value=float(p.price)) for p in points
        ]
        return IssueHistoryResponse(
            data_as_of=data_as_of,
            window=window,
            points=history_points,
        )

    if issue_id not in _FALLBACK_ISSUES:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    return IssueHistoryResponse(
        data_as_of=_NOW,
        window=window,
        points=[],
    )


def _issue_exists(issue_id: str, db: Session | None) -> bool:
    live = _resolve_live(db)
    if live is not None:
        live_issues, _ = live
        return _find_live(live_issues, issue_id) is not None
    return issue_id in _FALLBACK_ISSUES


@router.get(
    "/api/issues/{issue_id}/report",
    response_model=IssueReportResponse | ReportNotYetGenerated,
)
def get_issue_report(
    issue_id: str, db: Session | None = Depends(_get_optional_db)
) -> IssueReportResponse | ReportNotYetGenerated:
    live = _resolve_live(db)
    if live is not None and db is not None:
        live_issues, _ = live
        match = _find_live(live_issues, issue_id)
        if match is None:
            raise HTTPException(status_code=404, detail="Unknown issue id.")
        try:
            live_report = load_latest_successful_v4_report(db, match.market.id)
        except SQLAlchemyError:
            logger.warning(
                "FALLBACK: live report query failed, returning report empty state.",
                exc_info=True,
            )
            return ReportNotYetGenerated(status="not_yet_generated")
        if live_report is None:
            return ReportNotYetGenerated(status="not_yet_generated")

        try:
            return _issue_report_from_live(live_report, match)
        except (ValidationError, ValueError):
            logger.warning(
                "Live v4 report does not match its schema or stored evidence; "
                "returning report empty state.",
                exc_info=True,
            )
            return ReportNotYetGenerated(status="not_yet_generated")

    if issue_id not in _FALLBACK_ISSUES:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    return ReportNotYetGenerated(status="not_yet_generated")
