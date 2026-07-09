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

`/api/issues/{id}/report` reads the latest successful `ai_reports` row in
live mode. When no successful report exists, or when the report query fails,
it preserves the accepted `not_yet_generated` empty state. The static fallback
path keeps one demo-safe sample report when no live data is available.
"""
import logging
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.ai_report import PROMPT_VERSION
from app.core.category_taxonomy import category_matches
from app.core.config import settings
from app.db.queries import (
    LiveAiReport,
    LiveIssue,
    load_history_points,
    load_latest_successful_report,
    load_live_issues,
    load_related_events_for_market,
    load_signals_for_market,
)
from app.db.session import get_db
from app.schemas.issues import (
    HistoryPoint,
    IssueDetail,
    IssueHistoryResponse,
    IssueListResponse,
    IssueReportResponse,
    IssueSummary,
    RelatedEventCandidate,
    ReportContent,
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


def _issue_report_from_live(live_report: LiveAiReport) -> IssueReportResponse:
    return IssueReportResponse(
        id=str(live_report.report.id),
        generated_at=live_report.report.generated_at,
        data_as_of=live_report.data_as_of,
        status="success",
        content=ReportContent(**live_report.report.content),
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
            live_report = load_latest_successful_report(
                db,
                match.market.id,
                preferred_prompt_version=PROMPT_VERSION,
            )
        except SQLAlchemyError:
            logger.warning(
                "FALLBACK: live report query failed, returning report empty state.",
                exc_info=True,
            )
            return ReportNotYetGenerated(status="not_yet_generated")
        if live_report is None:
            return ReportNotYetGenerated(status="not_yet_generated")
        try:
            return _issue_report_from_live(live_report)
        except ValidationError:
            logger.warning(
                "Live report content does not match the current report schema; "
                "returning report empty state.",
                exc_info=True,
            )
            return ReportNotYetGenerated(status="not_yet_generated")

    if issue_id not in _FALLBACK_ISSUES:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    if issue_id != "b3f1c2a4-0000-4000-8000-000000000001":
        return ReportNotYetGenerated(status="not_yet_generated")
    return IssueReportResponse(
        id="7c2e1a90-0000-4000-8000-0000000000aa",
        generated_at=_NOW,
        data_as_of=_NOW,
        status="success",
        content=ReportContent(
            issue_explainer=(
                "이 이슈는 다자 기후 협정이 정해진 시점까지 비준되는지를 "
                "공개 데이터 맥락에서 살펴보는 항목입니다."
            ),
            why_it_matters=(
                "협정 비준 여부는 국제 환경 정책과 각국의 후속 절차를 "
                "이해하는 데 참고 맥락이 될 수 있습니다."
            ),
            current_reading=(
                "현재 공개 데이터에서는 이 이슈에 대한 재평가 흐름이 "
                "관측되고 있으나, 실제 결과를 뜻하지는 않습니다."
            ),
            scenario_major_change=(
                "조건이 명확히 성립하는 경우, 비준 절차가 확인되며 관련 "
                "정책 일정과 후속 이행 논의가 더 중요해질 수 있습니다."
            ),
            scenario_limited_change=(
                "관련 논의는 이어지지만 조건이 일부만 충족되는 경우, "
                "정책 관심은 유지되더라도 실제 절차 변화는 제한적일 수 있습니다."
            ),
            scenario_status_quo=(
                "조건이 성립하지 않는 경우, 기존 협상 또는 비준 절차가 "
                "대체로 유지되는 상황으로 해석할 수 있습니다."
            ),
            check_points=(
                "확인할 지점은 공식 비준 일정, 참여국 발표, 후속 절차의 "
                "진행 여부입니다."
            ),
            caution_note=(
                "이 요약은 공개 데이터와 등록된 맥락을 정리한 것이며, "
                "실제 결과에 대한 전망이나 행동 제안이 아닙니다."
            ),
        ),
    )
