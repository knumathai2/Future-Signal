"""Issues/signals/reports routes.

Live-data read path (TASK-010): reads markets / market_snapshots /
market_metrics / issue_signals / related_events through
app.db.session.get_db() (see app/db/queries.py for the query helpers).
Per ADR-051, this API reads issue data and may append a generation request plus
queued event. It never calls Polymarket or an AI provider directly.

FALLBACK NOTE: TASK-007/TASK-008 (the batch collector) had not produced any
market_snapshots/market_metrics rows as of this implementation, and
DATABASE_URL may also be unset entirely in local dev. Whenever there is no
live snapshot data to read, these routes fall back to the static sample
dataset below and log a "FALLBACK:" warning on every request, so this can
never become a silent, permanent substitute for live data - once TASK-008
produces real rows the live path takes over automatically, no code change
needed here. See reports/task-010-core-api-notes.md for detail.

`/api/issues/{id}/report` serves only a reconstructed successful v8 evidence
bundle and exposes honest idle/generating/fresh/stale/failure states. V1-v6
rows remain audit-only. Static fallback data never fabricates a report.
"""

import logging
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.ai_report import (
    ResolutionRulesInput,
    V4ContextSource,
    V4ReportInputs,
    V4VerifiedCandidateInput,
    V6StoredReportPayload,
    build_recent_history_summary,
    build_v6_stored_payload,
    run_v6_safety_and_semantic_checks,
)
from app.core.category_taxonomy import category_matches
from app.core.config import settings
from app.core.on_demand_briefing import (
    build_v8_input_bundle,
    enqueue_v8_request,
    latest_request_event,
    reconstruct_v8_report,
    v8_input_fingerprint,
)
from app.core.on_demand_worker_launcher import launch_on_demand_worker
from app.core.snapshot_metrics import as_utc_naive
from app.db.models import AiReport, AiReportGenerationRequest, Market
from app.db.queries import (
    LiveIssue,
    LiveV4AiReport,
    load_history_points,
    load_live_issue,
    load_live_issues,
    load_related_events_for_market,
    load_signals_for_market,
)
from app.db.session import get_db
from app.schemas.issues import (
    ContextCandidateOut,
    ContextSourceOut,
    GenerationRequestIn,
    GenerationRequestResponse,
    GenerationRequestStatusResponse,
    HistoryPoint,
    IssueDetail,
    IssueHistoryResponse,
    IssueListResponse,
    IssueReportResponse,
    IssueSummary,
    RelatedEventCandidate,
    ReportFailed,
    ReportGenerating,
    ReportIdle,
    SignalOut,
    V8IssueReportResponse,
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
            "Tracks reflected expectation on ratification of the multilateral climate accord."
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


def _resolve_live(
    db: Session | None, **query_options
) -> tuple[list[LiveIssue], datetime] | None:
    """Returns `(live_issues, data_as_of)` from the DB, or `None` if the
    caller should fall back to the static sample dataset."""
    if db is None:
        logger.warning("FALLBACK: DATABASE_URL is not set, serving static sample issue data.")
        return None
    try:
        result = load_live_issues(db, **query_options)
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


def _same_timestamp(left: datetime, right: datetime) -> bool:
    return as_utc_naive(left) == as_utc_naive(right)


def _not_after(left: datetime, right: datetime) -> bool:
    return as_utc_naive(left) <= as_utc_naive(right)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_issue_uuid(issue_id: str) -> UUID | None:
    try:
        return UUID(issue_id)
    except ValueError:
        return None


def _issue_report_from_live(
    live_report: LiveV4AiReport,
    live_issue: LiveIssue,
) -> IssueReportResponse:
    report = live_report.report
    metric = live_report.metric
    snapshot = live_report.snapshot
    payload = V6StoredReportPayload.model_validate(report.content)

    if report.input_metrics_id != metric.id or metric.market_id != live_issue.market.id:
        raise ValueError("V6 report metric does not belong to the requested issue")
    if not _not_after(snapshot.captured_at, report.generated_at):
        raise ValueError("V6 report data timestamp is later than generation")
    if not _not_after(payload.episode_at, report.generated_at):
        raise ValueError("V6 report episode is later than generation")
    if len(payload.context_candidate_ids) != len(set(payload.context_candidate_ids)):
        raise ValueError("V6 candidate IDs must be unique")

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
            or not _not_after(candidate.collected_at, report.generated_at)
            or not _not_after(report.generated_at, candidate.expires_at)
        ):
            raise ValueError("V6 candidate evidence is missing, expired, or not public")
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

    resolution_rules = None
    if payload.resolution_rules is not None:
        stored_rule = live_report.resolution_rule
        if stored_rule is None:
            raise ValueError("V6 stored resolution rule evidence is missing")
        resolution_rules = ResolutionRulesInput(
            condition_text=stored_rule.condition_text,
            deadline=_as_utc(stored_rule.deadline) if stored_rule.deadline else None,
            exclusions=list(stored_rule.exclusions or []),
            resolution_source=stored_rule.resolution_source,
            source_description_hash=stored_rule.source_description_hash,
            rules_hash=stored_rule.rules_hash,
            collected_at=_as_utc(stored_rule.collected_at),
        )
        if resolution_rules != payload.resolution_rules:
            raise ValueError("V6 resolution rule does not match stored evidence")

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
            _as_utc(live_issue.market.end_date) if live_issue.market.end_date is not None else None
        ),
        current_value=float(snapshot.price),
        change_24h=float(metric.change_24h) if metric.change_24h is not None else None,
        change_7d=float(metric.change_7d) if metric.change_7d is not None else None,
        confidence_level=metric.confidence_level,
        volume_24h=float(snapshot.volume_24h) if snapshot.volume_24h is not None else None,
        liquidity=float(snapshot.liquidity) if snapshot.liquidity is not None else None,
        context_candidates=candidate_inputs,
        resolution_rules=resolution_rules,
        value_24h_ago=(
            float(live_report.reference_24h.price) if live_report.reference_24h else None
        ),
        value_24h_ago_at=(
            _as_utc(live_report.reference_24h.captured_at) if live_report.reference_24h else None
        ),
        value_7d_ago=(float(live_report.reference_7d.price) if live_report.reference_7d else None),
        value_7d_ago_at=(
            _as_utc(live_report.reference_7d.captured_at) if live_report.reference_7d else None
        ),
        recent_history_summary=build_recent_history_summary(
            [
                (_as_utc(point.captured_at), float(point.price))
                for point in (live_report.recent_history or [])
            ]
        ),
    )
    expected_payload = build_v6_stored_payload(inputs, payload.briefing)
    validation = run_v6_safety_and_semantic_checks(payload, inputs, payload.briefing)
    if expected_payload != payload:
        raise ValueError("V6 deterministic content does not match stored evidence")
    if not validation.passed:
        raise ValueError(f"V6 semantic check failed: {validation.rule}")

    return IssueReportResponse(
        id=str(report.id),
        generated_at=_as_utc(report.generated_at),
        data_as_of=_as_utc(snapshot.captured_at),
        episode_at=_as_utc(payload.episode_at),
        status="success",
        report_version="v6",
        report_mode=payload.report_mode,
        observed_change=payload.observed_change.model_dump(),
        briefing=payload.briefing.model_dump(),
        resolution_reference=payload.resolution_reference.model_dump(),
        evidence_refs=payload.evidence_refs,
        context_candidates=candidate_outputs,
        relationship_boundary=payload.relationship_boundary,
        data_limitations=payload.data_limitations,
        caution_note=payload.caution_note,
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
    live = _resolve_live(
        db,
        window=window,
        sort=sort,
        limit=None if category else limit,
        offset=0 if category else offset,
    )
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

        if category:
            live_issues = sorted(live_issues, key=_sort_key)
            page = live_issues[offset : offset + limit]
        else:
            page = live_issues
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
    if db is not None:
        market_id = _parse_issue_uuid(issue_id)
        if market_id is not None:
            try:
                match = load_live_issue(db, market_id)
            except SQLAlchemyError:
                logger.warning(
                    "FALLBACK: live issue query failed, serving static sample issue data.",
                    exc_info=True,
                )
            else:
                if match is not None:
                    return _issue_detail_from_live(db, match, match.captured_at)

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
    if db is not None:
        market_id = _parse_issue_uuid(issue_id)
        if market_id is not None:
            try:
                match = load_live_issue(db, market_id)
            except SQLAlchemyError:
                logger.warning(
                    "FALLBACK: live issue query failed, serving static history data.",
                    exc_info=True,
                )
            else:
                if match is not None:
                    data_as_of = match.captured_at
                    since = data_as_of - _window_to_timedelta(window)
                    try:
                        points = load_history_points(db, match.market.id, since, data_as_of)
                    except SQLAlchemyError:
                        logger.warning(
                            "FALLBACK: live history query failed, returning empty history.",
                            exc_info=True,
                        )
                        points = []
                    history_points = [
                        HistoryPoint(captured_at=p.captured_at, value=float(p.price))
                        for p in points
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


def _latest_v8_reports(db: Session, market_id: UUID) -> list[AiReport]:
    return list(
        db.execute(
            select(AiReport)
            .where(
                AiReport.market_id == market_id,
                AiReport.status == "success",
                AiReport.prompt_version == "v8",
            )
            .order_by(AiReport.generated_at.desc(), AiReport.id.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )


def _latest_generation_request(
    db: Session,
    market_id: UUID,
) -> AiReportGenerationRequest | None:
    return db.execute(
        select(AiReportGenerationRequest)
        .where(
            AiReportGenerationRequest.market_id == market_id,
            AiReportGenerationRequest.prompt_version == "v8",
        )
        .order_by(
            AiReportGenerationRequest.requested_at.desc(),
            AiReportGenerationRequest.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def _successor_request_id(usage: dict | None) -> UUID | None:
    raw = usage.get("successor_request_id") if isinstance(usage, dict) else None
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _v8_public_report(
    db: Session,
    report: AiReport,
    *,
    current_fingerprint: str | None,
    latest_request: AiReportGenerationRequest | None,
) -> V8IssueReportResponse:
    payload = reconstruct_v8_report(db, report)
    latest_event = latest_request_event(db, latest_request.id) if latest_request else None
    cache_state = (
        "fresh" if current_fingerprint == payload.input_fingerprint else "stale"
    )
    public_status = cache_state
    request_id = None
    request_error = None
    if latest_request is not None and latest_event is not None:
        request_is_current = latest_request.input_fingerprint == current_fingerprint
        request_is_newer = not _not_after(latest_request.requested_at, report.generated_at)
        if request_is_current and latest_event.state in {"queued", "running"}:
            public_status = "generating"
            request_id = latest_request.id
        elif request_is_newer and latest_event.state == "failed":
            public_status = "failed_with_last_good"
            request_id = latest_request.id
            request_error = latest_event.error_code
    return V8IssueReportResponse(
        id=report.id,
        status=public_status,
        report_version="v8",
        headline=payload.writer.headline,
        summary=payload.writer.summary,
        sections=[section.model_dump(mode="json") for section in payload.writer.sections],
        sources=[source.model_dump(mode="json") for source in payload.sources],
        generated_at=_as_utc(report.generated_at),
        data_as_of=payload.data_as_of,
        context_as_of=payload.context_as_of,
        cache={
            "state": cache_state,
            "input_fingerprint": payload.input_fingerprint,
            "current_fingerprint": current_fingerprint,
        },
        data_limitations=payload.data_limitations,
        caution_note=payload.caution_note,
        request_id=request_id,
        request_error_code=request_error,
    )


@router.get(
    "/api/issues/{issue_id}/report",
    response_model=(
        V8IssueReportResponse | ReportIdle | ReportGenerating | ReportFailed
    ),
)
def get_issue_report(
    issue_id: str, db: Session | None = Depends(_get_optional_db)
) -> V8IssueReportResponse | ReportIdle | ReportGenerating | ReportFailed:
    if db is not None:
        market_id = _parse_issue_uuid(issue_id)
        if market_id is None:
            raise HTTPException(status_code=404, detail="Unknown issue id.")
        try:
            market = db.get(Market, market_id)
            if market is None:
                if issue_id in _FALLBACK_ISSUES:
                    return ReportIdle(status="idle")
                raise HTTPException(status_code=404, detail="Unknown issue id.")
            reports = _latest_v8_reports(db, market.id)
            latest_request = _latest_generation_request(db, market.id)
            current_bundle = build_v8_input_bundle(
                db,
                market.id,
                now=datetime.now(UTC),
            )
            current_fingerprint = (
                v8_input_fingerprint(current_bundle) if current_bundle is not None else None
            )
        except HTTPException:
            raise
        except SQLAlchemyError:
            logger.warning(
                "FALLBACK: live report query failed, returning report empty state.",
                exc_info=True,
            )
            return ReportIdle(status="idle")

        for report in reports:
            try:
                return _v8_public_report(
                    db,
                    report,
                    current_fingerprint=current_fingerprint,
                    latest_request=latest_request,
                )
            except (ValidationError, ValueError):
                logger.warning(
                    "Live v8 report does not match its schema or stored evidence; "
                    "trying the previous successful row.",
                    exc_info=True,
                )
        if latest_request is not None:
            latest_event = latest_request_event(db, latest_request.id)
            if latest_event is not None and latest_event.state in {"queued", "running"}:
                return ReportGenerating(
                    status="generating",
                    request_id=latest_request.id,
                    input_fingerprint=latest_request.input_fingerprint,
                    requested_at=_as_utc(latest_request.requested_at),
                )
            if latest_event is not None and latest_event.state == "failed":
                return ReportFailed(
                    status="failed",
                    request_id=latest_request.id,
                    error_code=latest_event.error_code or "generation_failed",
                )
            if latest_event is not None and latest_event.state == "succeeded":
                return ReportFailed(
                    status="failed",
                    request_id=latest_request.id,
                    error_code="stored_report_invalid",
                )
        return ReportIdle(status="idle")

    if issue_id not in _FALLBACK_ISSUES:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    return ReportIdle(status="idle")


@router.post(
    "/api/issues/{issue_id}/report/generate",
    response_model=GenerationRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_issue_report(
    issue_id: str,
    request_body: GenerationRequestIn,
    db: Session | None = Depends(_get_optional_db),
) -> GenerationRequestResponse:
    """Append or join a request; never call a provider in the API process."""
    if db is None:
        raise HTTPException(status_code=503, detail="Generation storage is unavailable.")
    market_id = _parse_issue_uuid(issue_id)
    if market_id is None:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    try:
        market = db.get(Market, market_id)
        if market is None:
            raise HTTPException(status_code=404, detail="Unknown issue id.")
        result = enqueue_v8_request(
            db,
            market.id,
            requested_by="user",
            context_refresh_requested=request_body.refresh_context,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Generation request failed.") from exc
    if result is None:
        raise HTTPException(status_code=409, detail="Current evidence bundle is unavailable.")
    if result.state == "queued":
        # Generation remains outside this API process. The child receives the
        # committed request ID and owns the provider call plus report write.
        launch_on_demand_worker(result.request_id, env=settings.env)
    request_status = "fresh" if result.state == "succeeded" else result.state
    return GenerationRequestResponse(
        request_id=result.request_id,
        status=request_status,
        created=result.created,
        input_fingerprint=result.input_fingerprint,
    )


@router.get(
    "/api/issues/{issue_id}/report/requests/{request_id}",
    response_model=GenerationRequestStatusResponse,
)
def get_generation_request_status(
    issue_id: str,
    request_id: UUID,
    db: Session | None = Depends(_get_optional_db),
) -> GenerationRequestStatusResponse:
    if db is None:
        raise HTTPException(status_code=503, detail="Generation storage is unavailable.")
    market_id = _parse_issue_uuid(issue_id)
    if market_id is None:
        raise HTTPException(status_code=404, detail="Unknown issue id.")
    request = db.get(AiReportGenerationRequest, request_id)
    if request is None or request.market_id != market_id:
        raise HTTPException(status_code=404, detail="Unknown generation request id.")
    latest = latest_request_event(db, request.id)
    if latest is None:
        raise HTTPException(status_code=409, detail="Generation request has no state event.")
    return GenerationRequestStatusResponse(
        request_id=request.id,
        issue_id=request.market_id,
        state=latest.state,
        attempt_number=latest.attempt_number,
        requested_at=_as_utc(request.requested_at),
        updated_at=_as_utc(latest.recorded_at),
        input_fingerprint=request.input_fingerprint,
        report_id=latest.report_id,
        error_code=latest.error_code,
        successor_request_id=_successor_request_id(latest.usage),
    )
