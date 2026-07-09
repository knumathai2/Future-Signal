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
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ai_report import (
    PROMPT_VERSION,
    LLMCallError,
    LLMClient,
    ReportPromptInputs,
    build_prompt,
    parse_report_content,
    run_safety_filter,
)
from app.core.snapshot_metrics import as_utc_naive
from app.db.models import AiReport, IssueSignal, Market, MarketMetric, MarketSnapshot, RelatedEvent

logger = logging.getLogger(__name__)

# Regeneration cost-control constants (Technical Design §9).
STALENESS_THRESHOLD = timedelta(hours=24)
MAX_REPORTS_PER_BATCH_RUN = 10
# One initial attempt + exactly one retry (Technical Design §10.6). Applies to
# both an LLM API timeout/error and a malformed/schema-mismatched response -
# neither is distinguished from the other for retry-budget purposes.
MAX_ATTEMPTS = 2


@dataclass
class ReportOutcome:
    market_id: uuid.UUID
    status: str  # "success" | "failed" | "filtered" | "skipped"
    reason: str | None = None


def _latest_successful_report(db: Session, market_id: uuid.UUID) -> AiReport | None:
    return db.execute(
        select(AiReport)
        .where(AiReport.market_id == market_id, AiReport.status == "success")
        .order_by(AiReport.generated_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def select_markets_for_regeneration(db: Session, run_timestamp: datetime) -> list[MarketMetric]:
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

    qualifying: list[MarketMetric] = []
    for metric in metrics:
        if metric.market_id in new_signal_market_ids:
            qualifying.append(metric)
            continue
        latest = _latest_successful_report(db, metric.market_id)
        if latest is None or as_utc_naive(latest.generated_at) < as_utc_naive(
            run_timestamp - STALENESS_THRESHOLD
        ):
            qualifying.append(metric)

    def _heat_score(metric: MarketMetric) -> float:
        return float(metric.heat_score) if metric.heat_score is not None else 0.0

    qualifying.sort(key=_heat_score, reverse=True)
    return qualifying[:MAX_REPORTS_PER_BATCH_RUN]


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


def _describe_related_event(db: Session, market_id: uuid.UUID) -> str | None:
    """First curated related-event candidate for this market, if any
    (Service Design §8: manually curated, 3-5 demo issues only)."""
    event = db.execute(
        select(RelatedEvent).where(RelatedEvent.market_id == market_id).limit(1)
    ).scalar_one_or_none()
    if event is None:
        return None
    return f"{event.event_title} ({event.event_date}): {event.note}"


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

    return ReportPromptInputs(
        title=market.title,
        description=market.description or "No description provided.",
        category=market.category,
        current_value=float(snapshot.price),
        change_24h=float(metric.change_24h) if metric.change_24h is not None else None,
        change_7d=float(metric.change_7d) if metric.change_7d is not None else None,
        confidence_level=metric.confidence_level,
        inflection_point_summary=_describe_inflection_point(db, market.id),
        related_event_or_none=_describe_related_event(db, market.id),
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

        content = parse_report_content(raw)
        if content is None:
            last_error = "malformed_or_schema_mismatched_response"
            logger.warning(
                "AI report attempt %s/%s produced a malformed/schema-mismatched "
                "response for market %s.",
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
    if not settings.openai_api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set. This script calls a paid external AI API "
            "using the project-approved OpenAI provider - set OPENAI_API_KEY "
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
        client = build_openai_client(settings.openai_api_key, settings.openai_model)
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
