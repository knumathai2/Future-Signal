"""AI report regeneration batch orchestration (Technical Design §9 / batch
step 8): decides which markets qualify for regeneration this run, caps to the
top 10 by `heat_score` for cost control, drives `app/core/ai_report.py`'s
prompt/LLM/parse/filter pipeline per market, and writes the outcome to
`ai_reports`.

Scope boundary: `app/core/ai_report.py` owns prompt building, the LLM call,
schema parsing, and the safety filter for one market in isolation (so it's
unit-testable with a fake `LLMClient` and no database). This module owns
*which* markets qualify, the per-run cap, retry-once orchestration, and the
`ai_reports` writes/failure logging.

Append-only rule (Technical Design §4.10): every call here either inserts one
new `ai_reports` row or inserts none at all - never updates a row in place.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.ai_report import (
    PROMPT_VERSION,
    V4_PROMPT_VERSION,
    V5_PROMPT_VERSION,
    V6_PROMPT_VERSION,
    LLMCallError,
    LLMClient,
    LLMUsage,
    ReportPromptInputs,
    ResolutionRulesInput,
    V4ContextSource,
    V4ReportInputs,
    V4StoredReportPayload,
    V4VerifiedCandidateInput,
    V5StoredReportPayload,
    V6StoredReportPayload,
    assemble_report_content,
    assemble_v4_report_content,
    assemble_v5_report_content,
    build_prompt,
    build_recent_history_summary,
    build_v4_prompt,
    build_v4_stored_payload,
    build_v5_prompt,
    build_v5_stored_payload,
    build_v6_prompt,
    build_v6_stored_payload,
    determine_v6_report_mode,
    parse_llm_fields,
    parse_v4_llm_fields,
    parse_v5_llm_fields,
    parse_v6_briefing,
    run_safety_filter,
    run_semantic_checks,
    run_v4_safety_and_semantic_checks,
    run_v5_safety_and_semantic_checks,
    run_v6_safety_and_semantic_checks,
)
from app.core.context_research_batch import APPROVED_BUDGET_USD, context_spend_usd
from app.core.snapshot_metrics import as_utc_naive
from app.db.models import (
    AiReport,
    ContextCandidate,
    ContextCollectionRun,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketResolutionRule,
    MarketSnapshot,
    RelatedEvent,
)

logger = logging.getLogger(__name__)

# Regeneration cost-control constants (Technical Design §9).
STALENESS_THRESHOLD = timedelta(hours=24)
MAX_REPORTS_PER_BATCH_RUN = 10
# One initial attempt + exactly one retry (Technical Design §10.6). Applies to
# both an LLM API timeout/error and a malformed/schema-mismatched response -
# neither is distinguished from the other for retry-budget purposes.
MAX_ATTEMPTS = 2


def _as_utc_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass
class ReportOutcome:
    market_id: uuid.UUID
    status: str  # "success" | "failed" | "filtered" | "skipped"
    reason: str | None = None
    model_usage: dict | None = None


def _latest_successful_report(
    db: Session,
    market_id: uuid.UUID,
    prompt_version: str = PROMPT_VERSION,
) -> AiReport | None:
    latest_current = db.execute(
        select(AiReport)
        .where(
            AiReport.market_id == market_id,
            AiReport.status == "success",
            AiReport.prompt_version == prompt_version,
        )
        .order_by(AiReport.generated_at.desc(), AiReport.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest_current is not None:
        return latest_current

    return db.execute(
        select(AiReport)
        .where(AiReport.market_id == market_id, AiReport.status == "success")
        .order_by(AiReport.generated_at.desc(), AiReport.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _sort_and_cap_qualifying_metrics(
    db: Session,
    metrics: list[MarketMetric],
    new_signal_market_ids: set[uuid.UUID],
    prompt_version: str = PROMPT_VERSION,
) -> list[MarketMetric]:
    qualifying: list[MarketMetric] = []
    for metric in metrics:
        if metric.market_id in new_signal_market_ids:
            qualifying.append(metric)
            continue
        latest = _latest_successful_report(db, metric.market_id, prompt_version)
        if (
            latest is None
            or latest.prompt_version != prompt_version
            or as_utc_naive(latest.generated_at)
            < as_utc_naive(metric.computed_at - STALENESS_THRESHOLD)
        ):
            qualifying.append(metric)

    def _heat_score(metric: MarketMetric) -> float:
        return float(metric.heat_score) if metric.heat_score is not None else 0.0

    qualifying.sort(key=_heat_score, reverse=True)
    return qualifying[:MAX_REPORTS_PER_BATCH_RUN]


def select_markets_for_regeneration(
    db: Session,
    run_timestamp: datetime,
    prompt_version: str = PROMPT_VERSION,
) -> list[MarketMetric]:
    """A market qualifies iff any of (Technical Design §9):
    - a new `issue_signals` row fired for it in *this* run (`triggered_at ==
      run_timestamp`, matching how `signal_detection.py` stamps new signals), or
    - it has no successful `ai_reports` row yet, or
    - its latest successful report is older than `STALENESS_THRESHOLD`.

    Capped to `MAX_REPORTS_PER_BATCH_RUN` by `heat_score` descending. Operates
    over this run's freshly computed `market_metrics` rows only, mirroring
    `signal_detection.detect_signals_for_run`'s same `computed_at ==
    run_timestamp` scoping."""
    metrics = (
        db.execute(select(MarketMetric).where(MarketMetric.computed_at == run_timestamp))
        .scalars()
        .all()
    )

    new_signal_market_ids = {
        row.market_id
        for row in db.execute(
            select(IssueSignal.market_id).where(IssueSignal.triggered_at == run_timestamp)
        )
    }

    return _sort_and_cap_qualifying_metrics(db, metrics, new_signal_market_ids, prompt_version)


def select_latest_metrics_for_regeneration(
    db: Session,
    prompt_version: str = PROMPT_VERSION,
) -> list[MarketMetric]:
    """Reports-only mode for the current DB state.

    Historical/demo seeding can leave each market's latest metric a few seconds
    apart, so a single global `max(computed_at)` timestamp is not a complete
    "current DB" view. This selector uses each market's own latest metric, then
    applies the same no-report/stale-report cap logic.
    """
    latest_metric_times = (
        select(
            MarketMetric.market_id.label("market_id"),
            func.max(MarketMetric.computed_at).label("computed_at"),
        )
        .group_by(MarketMetric.market_id)
        .subquery()
    )
    metrics = (
        db.execute(
            select(MarketMetric).join(
                latest_metric_times,
                and_(
                    MarketMetric.market_id == latest_metric_times.c.market_id,
                    MarketMetric.computed_at == latest_metric_times.c.computed_at,
                ),
            )
        )
        .scalars()
        .all()
    )

    latest_metric_by_market = {metric.market_id: metric.computed_at for metric in metrics}
    latest_market_ids = list(latest_metric_by_market)
    new_signal_market_ids = {
        market_id
        for market_id, triggered_at in db.execute(
            select(IssueSignal.market_id, IssueSignal.triggered_at).where(
                IssueSignal.market_id.in_(latest_market_ids)
            )
        )
        if latest_metric_by_market.get(market_id) == triggered_at
    }
    return _sort_and_cap_qualifying_metrics(db, metrics, new_signal_market_ids, prompt_version)


def _describe_inflection_point(db: Session, market_id: uuid.UUID) -> str | None:
    """Most recent `issue_signals` row for this market, if any, described
    deterministically from stored fields only - never fabricated."""
    signal = db.execute(
        select(IssueSignal)
        .where(IssueSignal.market_id == market_id)
        .order_by(IssueSignal.triggered_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if signal is None:
        return None
    magnitude_pp = float(signal.magnitude) * 100
    return f"A {magnitude_pp:+.1f}pp expectation shift was detected in the {signal.window} window."


def _find_related_event(db: Session, market_id: uuid.UUID) -> RelatedEvent | None:
    """First curated related-event candidate for this market, if any
    (Service Design §8: manually curated, 3-5 demo issues only). Returns the
    row itself so callers can use title/date and note as separate,
    non-duplicated inputs (ADR-033: `possible_drivers` uses title/date only,
    `external_context` uses the reviewed note only)."""
    return db.execute(
        select(RelatedEvent).where(RelatedEvent.market_id == market_id).limit(1)
    ).scalar_one_or_none()


def _find_tracked_outcome_label(db: Session, market_id: uuid.UUID) -> str | None:
    outcome = db.execute(
        select(MarketOutcome).where(
            MarketOutcome.market_id == market_id, MarketOutcome.is_tracked.is_(True)
        )
    ).scalar_one_or_none()
    return outcome.outcome_label if outcome is not None else None


def _latest_resolution_rules(db: Session, market_id: uuid.UUID) -> ResolutionRulesInput | None:
    row = db.execute(
        select(MarketResolutionRule)
        .where(MarketResolutionRule.market_id == market_id)
        .order_by(
            MarketResolutionRule.collected_at.desc(),
            MarketResolutionRule.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()
    if row is None:
        return None
    return ResolutionRulesInput(
        condition_text=row.condition_text,
        deadline=_as_utc_aware(row.deadline) if row.deadline else None,
        exclusions=list(row.exclusions or []),
        resolution_source=row.resolution_source,
        source_description_hash=row.source_description_hash,
        rules_hash=row.rules_hash,
        collected_at=_as_utc_aware(row.collected_at),
    )


def _reference_snapshot(
    db: Session,
    market_id: uuid.UUID,
    metric_timestamp: datetime,
    window: timedelta,
) -> MarketSnapshot | None:
    return db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == market_id,
            MarketSnapshot.captured_at <= metric_timestamp - window,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _recent_history_summary(db: Session, market_id: uuid.UUID, metric_timestamp: datetime):
    rows = db.execute(
        select(MarketSnapshot.captured_at, MarketSnapshot.price)
        .where(
            MarketSnapshot.market_id == market_id,
            MarketSnapshot.captured_at >= metric_timestamp - timedelta(days=7),
            MarketSnapshot.captured_at <= metric_timestamp,
        )
        .order_by(MarketSnapshot.captured_at.asc(), MarketSnapshot.id.asc())
    ).all()
    return build_recent_history_summary(
        [(_as_utc_aware(row.captured_at), float(row.price)) for row in rows]
    )


def build_prompt_inputs_for_market(
    db: Session, market: Market, metric: MarketMetric, run_timestamp: datetime
) -> ReportPromptInputs | None:
    """Returns `None` (never a fabricated value) if this metric has no usable
    snapshot at or before its timestamp - current_value has no other source."""
    metric_timestamp = metric.computed_at or run_timestamp
    snapshot = db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == market.id,
            MarketSnapshot.captured_at <= metric_timestamp,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if snapshot is None:
        return None

    related_event = _find_related_event(db, market.id)

    return ReportPromptInputs(
        title=market.title,
        description=market.description or "No description provided.",
        category=market.category,
        outcome_label=_find_tracked_outcome_label(db, market.id),
        end_date=market.end_date,
        current_value=float(snapshot.price),
        change_24h=float(metric.change_24h) if metric.change_24h is not None else None,
        change_7d=float(metric.change_7d) if metric.change_7d is not None else None,
        confidence_level=metric.confidence_level,
        inflection_point_summary=_describe_inflection_point(db, market.id),
        volume_24h=float(snapshot.volume_24h) if snapshot.volume_24h is not None else None,
        liquidity=float(snapshot.liquidity) if snapshot.liquidity is not None else None,
        related_event_title=related_event.event_title if related_event is not None else None,
        related_event_date=related_event.event_date if related_event is not None else None,
        related_event_note=related_event.note if related_event is not None else None,
    )


def generate_report_for_market(
    db: Session,
    market: Market,
    metric: MarketMetric,
    inputs: ReportPromptInputs,
    llm_client: LLMClient,
    run_timestamp: datetime,
    model_name: str,
) -> ReportOutcome:
    """Runs the build-prompt -> call -> parse -> filter -> store pipeline for
    one market. Filter failures are discarded entirely (no `ai_reports` row,
    no retry - Technical Design §10.4); call/parse failures get exactly one
    retry and then a `status=failed` row (Technical Design §10.6). Either way
    the previous successful report (if any) is left untouched and keeps
    serving, since this function never updates an existing row."""
    system_prompt, user_prompt = build_prompt(inputs)

    content = None
    last_error = "unknown"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = llm_client.complete(system_prompt, user_prompt)
        except LLMCallError as exc:
            last_error = str(exc)
            logger.warning(
                "AI report attempt %s/%s failed for market %s: %s",
                attempt,
                MAX_ATTEMPTS,
                market.id,
                last_error,
            )
            continue

        llm_fields = parse_llm_fields(raw)
        if llm_fields is None:
            last_error = "malformed_or_schema_mismatched_response"
            logger.warning(
                "AI report attempt %s/%s produced a malformed/schema-mismatched "
                "response for market %s.",
                attempt,
                MAX_ATTEMPTS,
                market.id,
            )
            continue

        content = assemble_report_content(inputs, llm_fields)
        if content is None:
            last_error = "assembled_content_failed_v3_bounds"
            logger.warning(
                "AI report attempt %s/%s produced content that failed ADR-033 "
                "structural validation for market %s.",
                attempt,
                MAX_ATTEMPTS,
                market.id,
            )
            continue
        break

    if content is None:
        db.add(
            AiReport(
                id=uuid.uuid4(),
                market_id=market.id,
                generated_at=run_timestamp,
                input_metrics_id=metric.id,
                content={},
                model_used=model_name,
                prompt_version=PROMPT_VERSION,
                status="failed",
            )
        )
        db.commit()
        logger.error(
            "AI report generation failed for market %s after %s attempt(s): %s. "
            "Previous successful report (if any) stays live.",
            market.id,
            MAX_ATTEMPTS,
            last_error,
        )
        return ReportOutcome(market_id=market.id, status="failed", reason=last_error)

    filter_result = run_safety_filter(content)
    if not filter_result.passed:
        logger.error(
            "AI report safety filter rejected market %s: field=%s rule=%s. "
            "Output discarded, not stored, not retried; previous successful "
            "report (if any) stays live.",
            market.id,
            filter_result.field,
            filter_result.rule,
        )
        return ReportOutcome(
            market_id=market.id,
            status="filtered",
            reason=f"{filter_result.field}:{filter_result.rule}",
        )

    semantic_result = run_semantic_checks(content, inputs)
    if not semantic_result.passed:
        logger.error(
            "AI report semantic check rejected market %s: field=%s rule=%s. "
            "Output discarded, not stored, not retried; previous successful "
            "report (if any) stays live.",
            market.id,
            semantic_result.field,
            semantic_result.rule,
        )
        return ReportOutcome(
            market_id=market.id,
            status="filtered",
            reason=f"{semantic_result.field}:{semantic_result.rule}",
        )

    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=market.id,
            generated_at=run_timestamp,
            input_metrics_id=metric.id,
            content=content.model_dump(),
            model_used=model_name,
            prompt_version=PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()
    return ReportOutcome(market_id=market.id, status="success")


def run_ai_report_batch(
    db: Session,
    run_timestamp: datetime,
    llm_client: LLMClient,
    model_name: str,
) -> list[ReportOutcome]:
    """Step 8 end to end for one batch run. Each market is isolated (its own
    try/except) so one bad market can't block the rest of the run, matching
    the pattern already used by `snapshot_metrics.insert_rows_with_fallback`
    and `signal_detection.detect_signals_for_run`."""
    qualifying_metrics = select_markets_for_regeneration(db, run_timestamp)

    outcomes: list[ReportOutcome] = []
    for metric in qualifying_metrics:
        market = db.get(Market, metric.market_id)
        if market is None:
            outcomes.append(
                ReportOutcome(
                    market_id=metric.market_id, status="skipped", reason="market_not_found"
                )
            )
            continue

        inputs = build_prompt_inputs_for_market(db, market, metric, run_timestamp)
        if inputs is None:
            logger.error(
                "Skipping AI report for market %s: no market_snapshots row at or "
                "before this metric timestamp.",
                market.id,
            )
            outcomes.append(
                ReportOutcome(
                    market_id=market.id,
                    status="skipped",
                    reason="no_snapshot_at_or_before_metric",
                )
            )
            continue

        try:
            outcome = generate_report_for_market(
                db, market, metric, inputs, llm_client, run_timestamp, model_name
            )
        except Exception:
            db.rollback()
            logger.exception("Unhandled error generating AI report for market %s.", market.id)
            outcomes.append(
                ReportOutcome(market_id=market.id, status="skipped", reason="unhandled_error")
            )
            continue
        outcomes.append(outcome)

    return outcomes


def run_ai_report_batch_for_latest_metrics(
    db: Session,
    llm_client: LLMClient,
    model_name: str,
) -> list[ReportOutcome]:
    """Generate reports from each market's latest metric row.

    Used by development/manual reports-only runs where "current DB state" means
    the latest available metric per market rather than one global batch
    timestamp.
    """
    outcomes: list[ReportOutcome] = []
    for metric in select_latest_metrics_for_regeneration(db):
        market = db.get(Market, metric.market_id)
        if market is None:
            outcomes.append(
                ReportOutcome(
                    market_id=metric.market_id, status="skipped", reason="market_not_found"
                )
            )
            continue

        inputs = build_prompt_inputs_for_market(db, market, metric, metric.computed_at)
        if inputs is None:
            logger.error(
                "Skipping AI report for market %s: no market_snapshots row at or "
                "before this metric timestamp.",
                market.id,
            )
            outcomes.append(
                ReportOutcome(
                    market_id=market.id,
                    status="skipped",
                    reason="no_snapshot_at_or_before_metric",
                )
            )
            continue

        try:
            outcome = generate_report_for_market(
                db,
                market,
                metric,
                inputs,
                llm_client,
                metric.computed_at,
                model_name,
            )
        except Exception:
            db.rollback()
            logger.exception("Unhandled error generating AI report for market %s.", market.id)
            outcomes.append(
                ReportOutcome(market_id=market.id, status="skipped", reason="unhandled_error")
            )
            continue
        outcomes.append(outcome)

    return outcomes


def _latest_completed_context_run(db: Session, market_id: uuid.UUID) -> ContextCollectionRun | None:
    return db.execute(
        select(ContextCollectionRun)
        .where(
            ContextCollectionRun.market_id == market_id,
            ContextCollectionRun.status.in_(["success", "no_candidate"]),
        )
        .order_by(
            ContextCollectionRun.finished_at.desc(),
            ContextCollectionRun.started_at.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def build_v4_inputs_for_market(
    db: Session,
    market: Market,
    metric: MarketMetric,
    run_timestamp: datetime,
) -> V4ReportInputs | None:
    """Load one metric snapshot and same-episode verified context only."""
    metric_timestamp = metric.computed_at or run_timestamp
    snapshot = db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == market.id,
            MarketSnapshot.captured_at <= metric_timestamp,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if snapshot is None:
        return None
    reference_24h = _reference_snapshot(db, market.id, metric_timestamp, timedelta(hours=24))
    reference_7d = _reference_snapshot(db, market.id, metric_timestamp, timedelta(days=7))

    context_run = _latest_completed_context_run(db, market.id)
    episode_at = context_run.episode_at if context_run is not None else metric_timestamp
    rows = (
        db.execute(
            select(ContextCandidate)
            .where(
                ContextCandidate.market_id == market.id,
                ContextCandidate.episode_at == episode_at,
                ContextCandidate.verification_state == "verified",
                ContextCandidate.expires_at >= run_timestamp,
            )
            .order_by(ContextCandidate.event_at.asc(), ContextCandidate.id.asc())
            .limit(3)
        )
        .scalars()
        .all()
    )
    candidates: list[V4VerifiedCandidateInput] = []
    for row in rows:
        if row.event_at is None or not row.sources:
            return None
        try:
            sources = [V4ContextSource.model_validate(source) for source in row.sources]
            candidates.append(
                V4VerifiedCandidateInput(
                    id=row.id,
                    title=row.event_title,
                    event_at=_as_utc_aware(row.event_at),
                    neutral_summary=row.neutral_summary,
                    sources=sources,
                )
            )
        except Exception:
            return None

    return V4ReportInputs(
        market_id=market.id,
        metric_id=metric.id,
        episode_at=_as_utc_aware(episode_at),
        data_as_of=_as_utc_aware(snapshot.captured_at),
        title=market.title,
        description=market.description or market.title,
        category=market.category,
        outcome_label=_find_tracked_outcome_label(db, market.id),
        end_date=_as_utc_aware(market.end_date) if market.end_date else None,
        current_value=float(snapshot.price),
        change_24h=float(metric.change_24h) if metric.change_24h is not None else None,
        change_7d=float(metric.change_7d) if metric.change_7d is not None else None,
        confidence_level=metric.confidence_level,
        volume_24h=float(snapshot.volume_24h) if snapshot.volume_24h is not None else None,
        liquidity=float(snapshot.liquidity) if snapshot.liquidity is not None else None,
        context_candidates=candidates,
        resolution_rules=_latest_resolution_rules(db, market.id),
        value_24h_ago=(float(reference_24h.price) if reference_24h is not None else None),
        value_24h_ago_at=(
            _as_utc_aware(reference_24h.captured_at) if reference_24h is not None else None
        ),
        value_7d_ago=(float(reference_7d.price) if reference_7d is not None else None),
        value_7d_ago_at=(
            _as_utc_aware(reference_7d.captured_at) if reference_7d is not None else None
        ),
        recent_history_summary=_recent_history_summary(db, market.id, metric_timestamp),
    )


def _usage_records(llm_client: LLMClient) -> list[LLMUsage]:
    records = getattr(llm_client, "usage_records", None)
    return records if isinstance(records, list) else []


def _usage_since(llm_client: LLMClient, start: int) -> dict:
    records = _usage_records(llm_client)[start:]
    costs = [record.cost_usd for record in records if record.cost_usd is not None]
    return {
        "writer_input_tokens": sum(record.input_tokens for record in records),
        "writer_output_tokens": sum(record.output_tokens for record in records),
        "writer_cost_usd": round(sum(costs), 8) if costs else None,
    }


def generate_v4_report_for_market(
    db: Session,
    market: Market,
    metric: MarketMetric,
    inputs: V4ReportInputs,
    llm_client: LLMClient,
    generated_at: datetime,
    model_name: str,
) -> ReportOutcome:
    """Generate and append one strict evidence-grounded v4 report."""
    system_prompt, user_prompt = build_v4_prompt(inputs)
    usage_start = len(_usage_records(llm_client))
    payload: V4StoredReportPayload | None = None
    llm_fields = None
    last_error = "unknown"
    for _attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = llm_client.complete(system_prompt, user_prompt)
        except LLMCallError as exc:
            last_error = type(exc).__name__
            continue
        llm_fields = parse_v4_llm_fields(raw)
        if llm_fields is None:
            last_error = "malformed_or_schema_mismatched_response"
            continue
        content = assemble_v4_report_content(inputs, llm_fields)
        if content is None:
            last_error = "assembled_content_failed_v4_contract"
            continue
        payload = build_v4_stored_payload(inputs, content)
        break

    usage = _usage_since(llm_client, usage_start)
    if payload is None or llm_fields is None:
        db.add(
            AiReport(
                id=uuid.uuid4(),
                market_id=market.id,
                generated_at=generated_at,
                input_metrics_id=metric.id,
                content={},
                model_used=model_name,
                prompt_version=V4_PROMPT_VERSION,
                status="failed",
            )
        )
        db.commit()
        return ReportOutcome(
            market_id=market.id,
            status="failed",
            reason=last_error,
            model_usage=usage,
        )

    validation = run_v4_safety_and_semantic_checks(payload, inputs, llm_fields)
    if not validation.passed:
        return ReportOutcome(
            market_id=market.id,
            status="filtered",
            reason=f"{validation.field}:{validation.rule}",
            model_usage=usage,
        )

    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=market.id,
            generated_at=generated_at,
            input_metrics_id=metric.id,
            content=payload.model_dump(mode="json"),
            model_used=model_name,
            prompt_version=V4_PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()
    return ReportOutcome(market_id=market.id, status="success", model_usage=usage)


def _run_v4_metrics(
    db: Session,
    metrics: list[MarketMetric],
    llm_client: LLMClient,
    model_name: str,
    *,
    generated_at_for_metric,
    failed_context_market_ids: set[uuid.UUID] | None = None,
    budget_usd: float = APPROVED_BUDGET_USD,
    writer_cost_reservation_usd: float = 0.5,
) -> list[ReportOutcome]:
    failed_context_market_ids = failed_context_market_ids or set()
    outcomes: list[ReportOutcome] = []
    running_spend = context_spend_usd(db)
    effective_budget = min(budget_usd, APPROVED_BUDGET_USD)
    for metric in metrics:
        if metric.market_id in failed_context_market_ids:
            outcomes.append(
                ReportOutcome(
                    market_id=metric.market_id,
                    status="skipped",
                    reason="context_research_failed",
                )
            )
            continue
        if running_spend + writer_cost_reservation_usd > effective_budget:
            outcomes.append(
                ReportOutcome(
                    market_id=metric.market_id,
                    status="skipped",
                    reason="budget_limit",
                )
            )
            continue
        market = db.get(Market, metric.market_id)
        if market is None:
            outcomes.append(
                ReportOutcome(
                    market_id=metric.market_id,
                    status="skipped",
                    reason="market_not_found",
                )
            )
            continue
        generated_at = generated_at_for_metric(metric)
        inputs = build_v4_inputs_for_market(db, market, metric, generated_at)
        if inputs is None:
            outcomes.append(
                ReportOutcome(
                    market_id=market.id,
                    status="skipped",
                    reason="invalid_or_missing_v4_evidence",
                )
            )
            continue
        try:
            outcome = generate_v4_report_for_market(
                db,
                market,
                metric,
                inputs,
                llm_client,
                generated_at,
                model_name,
            )
        except Exception:
            db.rollback()
            logger.exception("Unhandled error generating v4 report for market %s.", market.id)
            outcome = ReportOutcome(
                market_id=market.id,
                status="skipped",
                reason="unhandled_error",
            )
        outcomes.append(outcome)
        if outcome.model_usage:
            cost = outcome.model_usage.get("writer_cost_usd")
            if isinstance(cost, int | float):
                running_spend += float(cost)
    return outcomes


def run_v4_ai_report_batch(
    db: Session,
    run_timestamp: datetime,
    llm_client: LLMClient,
    model_name: str,
    *,
    failed_context_market_ids: set[uuid.UUID] | None = None,
    budget_usd: float = APPROVED_BUDGET_USD,
    writer_cost_reservation_usd: float = 0.5,
) -> list[ReportOutcome]:
    metrics = select_markets_for_regeneration(db, run_timestamp, V4_PROMPT_VERSION)
    return _run_v4_metrics(
        db,
        metrics,
        llm_client,
        model_name,
        generated_at_for_metric=lambda _metric: run_timestamp,
        failed_context_market_ids=failed_context_market_ids,
        budget_usd=budget_usd,
        writer_cost_reservation_usd=writer_cost_reservation_usd,
    )


def run_v4_ai_report_batch_for_latest_metrics(
    db: Session,
    llm_client: LLMClient,
    model_name: str,
    *,
    failed_context_market_ids: set[uuid.UUID] | None = None,
    budget_usd: float = APPROVED_BUDGET_USD,
    writer_cost_reservation_usd: float = 0.5,
) -> list[ReportOutcome]:
    metrics = select_latest_metrics_for_regeneration(db, V4_PROMPT_VERSION)
    return _run_v4_metrics(
        db,
        metrics,
        llm_client,
        model_name,
        generated_at_for_metric=lambda _metric: datetime.now(UTC),
        failed_context_market_ids=failed_context_market_ids,
        budget_usd=budget_usd,
        writer_cost_reservation_usd=writer_cost_reservation_usd,
    )


def generate_v5_report_for_market(
    db: Session,
    market: Market,
    metric: MarketMetric,
    inputs: V4ReportInputs,
    llm_client: LLMClient,
    generated_at: datetime,
    model_name: str,
) -> ReportOutcome:
    """Generate and append one ADR-048 evidence-bounded narrative report."""
    system_prompt, user_prompt = build_v5_prompt(inputs)
    usage_start = len(_usage_records(llm_client))
    payload: V5StoredReportPayload | None = None
    llm_fields = None
    last_error = "unknown"
    for _attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = llm_client.complete(system_prompt, user_prompt)
        except LLMCallError as exc:
            last_error = type(exc).__name__
            continue
        llm_fields = parse_v5_llm_fields(raw)
        if llm_fields is None:
            last_error = "malformed_or_schema_mismatched_response"
            continue
        content = assemble_v5_report_content(inputs, llm_fields)
        if content is None:
            last_error = "assembled_content_failed_v5_contract"
            continue
        payload = build_v5_stored_payload(inputs, content)
        break

    usage = _usage_since(llm_client, usage_start)
    if payload is None or llm_fields is None:
        db.add(
            AiReport(
                id=uuid.uuid4(),
                market_id=market.id,
                generated_at=generated_at,
                input_metrics_id=metric.id,
                content={},
                model_used=model_name,
                prompt_version=V5_PROMPT_VERSION,
                status="failed",
            )
        )
        db.commit()
        return ReportOutcome(
            market_id=market.id,
            status="failed",
            reason=last_error,
            model_usage=usage,
        )

    validation = run_v5_safety_and_semantic_checks(payload, inputs, llm_fields)
    if not validation.passed:
        return ReportOutcome(
            market_id=market.id,
            status="filtered",
            reason=f"{validation.field}:{validation.rule}",
            model_usage=usage,
        )

    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=market.id,
            generated_at=generated_at,
            input_metrics_id=metric.id,
            content=payload.model_dump(mode="json"),
            model_used=model_name,
            prompt_version=V5_PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()
    return ReportOutcome(market_id=market.id, status="success", model_usage=usage)


def _run_v5_metrics(
    db: Session,
    metrics: list[MarketMetric],
    llm_client: LLMClient,
    model_name: str,
    *,
    generated_at_for_metric,
    failed_context_market_ids: set[uuid.UUID] | None = None,
    budget_usd: float = APPROVED_BUDGET_USD,
    writer_cost_reservation_usd: float = 0.5,
) -> list[ReportOutcome]:
    failed_context_market_ids = failed_context_market_ids or set()
    outcomes: list[ReportOutcome] = []
    running_spend = context_spend_usd(db)
    effective_budget = min(budget_usd, APPROVED_BUDGET_USD)
    for metric in metrics:
        if metric.market_id in failed_context_market_ids:
            outcomes.append(ReportOutcome(metric.market_id, "skipped", "context_research_failed"))
            continue
        if running_spend + writer_cost_reservation_usd > effective_budget:
            outcomes.append(ReportOutcome(metric.market_id, "skipped", "budget_limit"))
            continue
        market = db.get(Market, metric.market_id)
        if market is None:
            outcomes.append(ReportOutcome(metric.market_id, "skipped", "market_not_found"))
            continue
        generated_at = generated_at_for_metric(metric)
        inputs = build_v4_inputs_for_market(db, market, metric, generated_at)
        if inputs is None:
            outcomes.append(
                ReportOutcome(metric.market_id, "skipped", "invalid_or_missing_v5_evidence")
            )
            continue
        try:
            outcome = generate_v5_report_for_market(
                db, market, metric, inputs, llm_client, generated_at, model_name
            )
        except Exception:
            db.rollback()
            logger.exception("Unhandled error generating v5 report for market %s.", market.id)
            outcome = ReportOutcome(market.id, "skipped", "unhandled_error")
        outcomes.append(outcome)
        if outcome.model_usage:
            cost = outcome.model_usage.get("writer_cost_usd")
            if isinstance(cost, int | float):
                running_spend += float(cost)
    return outcomes


def run_v5_ai_report_batch(
    db: Session,
    run_timestamp: datetime,
    llm_client: LLMClient,
    model_name: str,
    **kwargs,
) -> list[ReportOutcome]:
    metrics = select_markets_for_regeneration(db, run_timestamp, V5_PROMPT_VERSION)
    return _run_v5_metrics(
        db,
        metrics,
        llm_client,
        model_name,
        generated_at_for_metric=lambda _metric: run_timestamp,
        **kwargs,
    )


def run_v5_ai_report_batch_for_latest_metrics(
    db: Session,
    llm_client: LLMClient,
    model_name: str,
    **kwargs,
) -> list[ReportOutcome]:
    metrics = select_latest_metrics_for_regeneration(db, V5_PROMPT_VERSION)
    return _run_v5_metrics(
        db,
        metrics,
        llm_client,
        model_name,
        generated_at_for_metric=lambda _metric: datetime.now(UTC),
        **kwargs,
    )


def generate_v6_report_for_market(
    db: Session,
    market: Market,
    metric: MarketMetric,
    inputs: V4ReportInputs,
    llm_client: LLMClient,
    generated_at: datetime,
    model_name: str,
) -> ReportOutcome:
    """Generate and append one ADR-050 mode-constrained v6 report."""
    mode = determine_v6_report_mode(inputs)
    system_prompt, user_prompt = build_v6_prompt(inputs)
    usage_start = len(_usage_records(llm_client))
    payload: V6StoredReportPayload | None = None
    briefing = None
    last_error = "unknown"
    for _attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = llm_client.complete(system_prompt, user_prompt)
        except LLMCallError as exc:
            last_error = type(exc).__name__
            continue
        briefing = parse_v6_briefing(raw, mode)
        if briefing is None:
            last_error = "malformed_mode_or_schema_mismatched_response"
            continue
        payload = build_v6_stored_payload(inputs, briefing)
        if payload is None:
            last_error = "assembled_content_failed_v6_contract"
            continue
        break

    usage = _usage_since(llm_client, usage_start)
    if payload is None or briefing is None:
        db.add(
            AiReport(
                id=uuid.uuid4(),
                market_id=market.id,
                generated_at=generated_at,
                input_metrics_id=metric.id,
                content={},
                model_used=model_name,
                prompt_version=V6_PROMPT_VERSION,
                status="failed",
            )
        )
        db.commit()
        return ReportOutcome(
            market_id=market.id,
            status="failed",
            reason=last_error,
            model_usage=usage,
        )

    validation = run_v6_safety_and_semantic_checks(payload, inputs, briefing)
    if not validation.passed:
        return ReportOutcome(
            market_id=market.id,
            status="filtered",
            reason=f"{validation.field}:{validation.rule}",
            model_usage=usage,
        )

    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=market.id,
            generated_at=generated_at,
            input_metrics_id=metric.id,
            content=payload.model_dump(mode="json"),
            model_used=model_name,
            prompt_version=V6_PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()
    return ReportOutcome(market_id=market.id, status="success", model_usage=usage)


def _run_v6_metrics(
    db: Session,
    metrics: list[MarketMetric],
    llm_client: LLMClient,
    model_name: str,
    *,
    generated_at_for_metric,
    failed_context_market_ids: set[uuid.UUID] | None = None,
    budget_usd: float = APPROVED_BUDGET_USD,
    writer_cost_reservation_usd: float = 0.5,
) -> list[ReportOutcome]:
    failed_context_market_ids = failed_context_market_ids or set()
    outcomes: list[ReportOutcome] = []
    running_spend = context_spend_usd(db)
    effective_budget = min(budget_usd, APPROVED_BUDGET_USD)
    for metric in metrics:
        if metric.market_id in failed_context_market_ids:
            outcomes.append(ReportOutcome(metric.market_id, "skipped", "context_research_failed"))
            continue
        if running_spend + writer_cost_reservation_usd > effective_budget:
            outcomes.append(ReportOutcome(metric.market_id, "skipped", "budget_limit"))
            continue
        market = db.get(Market, metric.market_id)
        if market is None:
            outcomes.append(ReportOutcome(metric.market_id, "skipped", "market_not_found"))
            continue
        generated_at = generated_at_for_metric(metric)
        inputs = build_v4_inputs_for_market(db, market, metric, generated_at)
        if inputs is None:
            outcomes.append(
                ReportOutcome(metric.market_id, "skipped", "invalid_or_missing_v6_evidence")
            )
            continue
        try:
            outcome = generate_v6_report_for_market(
                db, market, metric, inputs, llm_client, generated_at, model_name
            )
        except Exception:
            db.rollback()
            logger.exception("Unhandled error generating v6 report for market %s.", market.id)
            outcome = ReportOutcome(market.id, "skipped", "unhandled_error")
        outcomes.append(outcome)
        if outcome.model_usage:
            cost = outcome.model_usage.get("writer_cost_usd")
            if isinstance(cost, int | float):
                running_spend += float(cost)
    return outcomes


def run_v6_ai_report_batch(
    db: Session,
    run_timestamp: datetime,
    llm_client: LLMClient,
    model_name: str,
    **kwargs,
) -> list[ReportOutcome]:
    metrics = select_markets_for_regeneration(db, run_timestamp, V6_PROMPT_VERSION)
    return _run_v6_metrics(
        db,
        metrics,
        llm_client,
        model_name,
        generated_at_for_metric=lambda _metric: run_timestamp,
        **kwargs,
    )


def run_v6_ai_report_batch_for_latest_metrics(
    db: Session,
    llm_client: LLMClient,
    model_name: str,
    **kwargs,
) -> list[ReportOutcome]:
    metrics = select_latest_metrics_for_regeneration(db, V6_PROMPT_VERSION)
    return _run_v6_metrics(
        db,
        metrics,
        llm_client,
        model_name,
        generated_at_for_metric=lambda _metric: datetime.now(UTC),
        **kwargs,
    )


if __name__ == "__main__":
    from app.core.ai_report import build_openai_client
    from app.core.config import settings
    from app.db.session import get_session_factory

    if not settings.database_url:
        raise SystemExit(
            "DATABASE_URL is not set. This script writes to a real database and "
            "requires an approved local/dev Postgres instance per AGENTS.md - "
            "set DATABASE_URL before running. For a DB-free dry run, see "
            "backend/tests/test_ai_report_batch.py, which exercises the same "
            "pipeline against an in-memory SQLite database with a fake LLM client."
        )
    if not settings.ai_api_key:
        raise SystemExit(
            "OPENAI_API_KEY or OPENROUTER_API_KEY is not set. This script calls a "
            "paid external AI API using the project-approved provider - set a key "
            "before running."
        )

    from sqlalchemy import func

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
        extra_headers = {}
        if settings.ai_provider == "openrouter":
            if settings.openrouter_http_referer:
                extra_headers["HTTP-Referer"] = settings.openrouter_http_referer
            if settings.openrouter_app_title:
                extra_headers["X-OpenRouter-Title"] = settings.openrouter_app_title
        client = build_openai_client(
            settings.ai_api_key,
            settings.openai_model,
            base_url=settings.ai_base_url,
            provider_name=settings.ai_provider,
            extra_headers=extra_headers,
        )
        results = run_ai_report_batch(session, latest_run, client, settings.openai_model)
    finally:
        session.close()

    seen_statuses = {r.status for r in results}
    status_counts = {
        status: sum(1 for r in results if r.status == status) for status in seen_statuses
    }
    logger.info(
        "AI report batch for run %s: %s outcome(s) - %s", latest_run, len(results), status_counts
    )
