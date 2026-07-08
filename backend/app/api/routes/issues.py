"""Issues/signals/reports routes.

DRAFT STATUS: this router returns hardcoded sample data, not live Postgres
reads. TASK-002's schema is not yet applied to any database, so there is
nothing to query yet. Wiring these handlers to app.db.session.get_db()
happens once TASK-002 is approved and migrated - the response_model shapes
below are the actual contract and should not change at that point.

Per Technical Design §3 / AGENTS.md: this API layer must never call
Polymarket or an AI provider directly, even after DB wiring lands.
"""
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query

from app.schemas.issues import (
    HistoryPoint,
    IssueDetail,
    IssueHistoryResponse,
    IssueListResponse,
    IssueReportResponse,
    IssueSummary,
    ReportContent,
    ReportNotYetGenerated,
    SignalOut,
)

router = APIRouter(tags=["issues"])

_NOW = datetime(2026, 7, 8, 9, 0, 0, tzinfo=UTC)

# Sample data illustrating the contract shape only - not real Polymarket data.
_SAMPLE_ISSUES: dict[str, IssueDetail] = {
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


@router.get("/api/issues", response_model=IssueListResponse)
def list_issues(
    category: str | None = Query(default=None),
    window: str = Query(default="24h", pattern="^(24h|7d)$"),
    sort: str = Query(default="heat", pattern="^(heat|change|recent)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> IssueListResponse:
    issues = list(_SAMPLE_ISSUES.values())
    if category:
        issues = [i for i in issues if i.category == category]
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
def get_issue(issue_id: str) -> IssueDetail:
    issue = _SAMPLE_ISSUES.get(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    return issue


@router.get("/api/issues/{issue_id}/history", response_model=IssueHistoryResponse)
def get_issue_history(
    issue_id: str, window: str = Query(default="24h", pattern="^(24h|7d|30d)$")
) -> IssueHistoryResponse:
    if issue_id not in _SAMPLE_ISSUES:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    return IssueHistoryResponse(
        data_as_of=_NOW,
        window=window,
        points=[
            HistoryPoint(captured_at=_NOW, value=_SAMPLE_ISSUES[issue_id].current_value)
        ],
    )


@router.get(
    "/api/issues/{issue_id}/report",
    response_model=IssueReportResponse | ReportNotYetGenerated,
)
def get_issue_report(issue_id: str) -> IssueReportResponse | ReportNotYetGenerated:
    if issue_id not in _SAMPLE_ISSUES:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    if issue_id != "b3f1c2a4-0000-4000-8000-000000000001":
        # See API_CONTRACT.md "Open item" - returned as 200 with a status
        # field rather than a bodyless 204, since HTTP 204 cannot carry a
        # response body. Flagged for PM confirmation.
        return ReportNotYetGenerated(status="not_yet_generated")
    return IssueReportResponse(
        id="7c2e1a90-0000-4000-8000-0000000000aa",
        generated_at=_NOW,
        data_as_of=_NOW,
        status="success",
        content=ReportContent(
            issue_summary=(
                "Reflected expectation for ratification has risen over "
                "the past 24 hours."
            ),
            movement_explanation=(
                "The change coincides with increased public data "
                "activity on this issue."
            ),
            key_change_context=(
                "Change magnitude crossed the expectation-shift "
                "threshold for the 24h window."
            ),
            uncertainty_summary=(
                "Data reliability is sufficient for this window; "
                "interpret recent movements cautiously."
            ),
            neutral_conclusion=(
                "This reflects a shift in public expectation data, "
                "not a predicted outcome."
            ),
        ),
    )
