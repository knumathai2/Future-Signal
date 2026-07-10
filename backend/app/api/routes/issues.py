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
        report_version="v3",
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
                preferred_prompt_version="v3",
            )
        except SQLAlchemyError:
            logger.warning(
                "FALLBACK: live report query failed, returning report empty state.",
                exc_info=True,
            )
            return ReportNotYetGenerated(status="not_yet_generated")
        if live_report is None:
            return ReportNotYetGenerated(status="not_yet_generated")

        if (
            live_report.data_as_of is None
            or live_report.data_as_of > live_report.report.generated_at
        ):
            logger.warning(
                "Report data_as_of is unavailable or in the future compared to generated_at; "
                "returning report empty state."
            )
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
        report_version="v3",
        content=ReportContent(
            issue_overview="이 이슈는 공개된 기한까지 문서에 적힌 조건이 충족되는지를 추적합니다.",
            current_data_reading=(
                "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 63%이며, "
                "24시간 전보다 8.2퍼센트포인트 높게 관찰되었습니다."
            ),
            possible_outlook=(
                "이후 공개 데이터에서 관찰된 움직임의 지속, 확대 또는 완화가 확인되더라도, "
                "이는 데이터의 흐름만 설명하며 현실의 결과나 변화의 이유를 입증하지 않습니다."
            ),
            possible_drivers=(
                "이 움직임과 함께 비교할 수 있도록 수동 검토를 마친 맥락 후보가 없습니다. "
                "현재 데이터는 관찰된 움직임만 보여 주며, 추가 맥락은 다른 자료를 통해 "
                "독립적으로 확인해야 합니다."
            ),
            external_context=None,
            what_to_check=(
                "게시된 이슈 문구와 기록된 기한, 데이터 기준 시각, "
                "이후 공개 데이터 갱신 내용을 추가로 확인해야 합니다."
            ),
            data_limitations=(
                "이 읽기는 활동량, 유동성, 24시간 변화 폭, 24시간 및 "
                "7일 이력 범위의 영향을 받습니다. "
                "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다."
            ),
            caution_note=(
                "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, "
                "전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. "
                "24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 않으며 "
                "24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, "
                "다른 자료를 통해 독립적으로 확인해야 합니다."
            ),
        ),
    )
