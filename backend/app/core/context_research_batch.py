"""Per-market context research, verification, and append-only storage.

TASK-060 places this stage after signal detection and before report generation.
Each market commits or rolls back independently. Provider failures keep prior
successful candidates and reports untouched; ``no_candidate`` is a normal
completed state.
"""

import logging
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlparse

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context_research import ContextResearchResult, ResearchInputs, ResearchUsage
from app.core.context_verification import (
    IndependentVerifierClient,
    VerificationDecision,
    verify_research_result,
)
from app.core.snapshot_metrics import as_utc_naive
from app.db.models import (
    ContextCandidate,
    ContextCollectionRun,
    DataCollectionLog,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketResolutionRule,
    MarketSnapshot,
)

logger = logging.getLogger(__name__)

DEFAULT_CHANGE_THRESHOLD = 0.05
DEFAULT_STALENESS = timedelta(hours=24)
DEFAULT_SEARCH_WINDOW = timedelta(hours=24)
TOP_HEAT_LIMIT = 10
MAX_PUBLIC_CANDIDATES = 3
APPROVED_BUDGET_USD = 100.0
DEFAULT_COST_RESERVATION_USD = 2.0
WITHHELD_SUMMARY = "검증 조건을 모두 충족하지 않아 공개 경로에서 제외된 후보입니다."


class ContextResearchService(Protocol):
    def research(self, inputs: ResearchInputs) -> ContextResearchResult: ...


@dataclass(frozen=True)
class ContextResearchTarget:
    market_id: uuid.UUID
    metric_id: int
    episode_at: datetime
    inflection_at: datetime | None
    reasons: tuple[str, ...]


@dataclass
class ContextResearchOutcome:
    market_id: uuid.UUID
    status: str
    accepted_count: int = 0
    candidate_ids: list[uuid.UUID] = field(default_factory=list)
    reason: str | None = None


def _as_utc_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _latest_metrics(db: Session) -> list[MarketMetric]:
    latest_times = (
        select(
            MarketMetric.market_id.label("market_id"),
            func.max(MarketMetric.computed_at).label("computed_at"),
        )
        .group_by(MarketMetric.market_id)
        .subquery()
    )
    return (
        db.execute(
            select(MarketMetric).join(
                latest_times,
                and_(
                    MarketMetric.market_id == latest_times.c.market_id,
                    MarketMetric.computed_at == latest_times.c.computed_at,
                ),
            )
        )
        .scalars()
        .all()
    )


def select_context_targets(
    db: Session,
    run_timestamp: datetime,
    *,
    use_latest_metrics: bool = False,
    backfill: bool = False,
    change_threshold: float = DEFAULT_CHANGE_THRESHOLD,
    staleness: timedelta = DEFAULT_STALENESS,
    top_heat_limit: int = TOP_HEAT_LIMIT,
) -> list[ContextResearchTarget]:
    """Select signal/change/heat/stale targets in deterministic heat order."""
    metrics = (
        _latest_metrics(db)
        if use_latest_metrics or backfill
        else (
            db.execute(select(MarketMetric).where(MarketMetric.computed_at == run_timestamp))
            .scalars()
            .all()
        )
    )
    metrics.sort(
        key=lambda metric: (
            float(metric.heat_score) if metric.heat_score is not None else 0.0,
            str(metric.market_id),
        ),
        reverse=True,
    )
    top_heat_ids = {metric.market_id for metric in metrics[: max(top_heat_limit, 0)]}
    reference_time = _as_utc_aware(run_timestamp)

    targets: list[ContextResearchTarget] = []
    for metric in metrics:
        reasons: list[str] = []
        metric_time = _as_utc_aware(metric.computed_at)
        signal_time = db.execute(
            select(func.max(IssueSignal.triggered_at)).where(
                IssueSignal.market_id == metric.market_id,
                IssueSignal.triggered_at <= metric.computed_at,
            )
        ).scalar_one_or_none()
        if signal_time is not None and as_utc_naive(signal_time) == as_utc_naive(
            metric.computed_at
        ):
            reasons.append("new_expectation_shift")
        if metric.change_24h is not None and abs(float(metric.change_24h)) >= change_threshold:
            reasons.append("absolute_change_threshold")
        if metric.market_id in top_heat_ids:
            reasons.append("top_heat")

        latest_verified = db.execute(
            select(func.max(ContextCandidate.collected_at)).where(
                ContextCandidate.market_id == metric.market_id,
                ContextCandidate.verification_state == "verified",
            )
        ).scalar_one_or_none()
        if latest_verified is None:
            reasons.append("missing_verified_context")
        elif _as_utc_aware(latest_verified) < reference_time - staleness:
            reasons.append("stale_verified_context")
        if backfill:
            reasons.append("backfill")

        if reasons:
            inflection_at = _as_utc_aware(signal_time) if signal_time is not None else None
            targets.append(
                ContextResearchTarget(
                    market_id=metric.market_id,
                    metric_id=metric.id,
                    episode_at=inflection_at or metric_time,
                    inflection_at=inflection_at,
                    reasons=tuple(dict.fromkeys(reasons)),
                )
            )
    return targets


def build_research_inputs(
    db: Session,
    target: ContextResearchTarget,
    *,
    search_window: timedelta = DEFAULT_SEARCH_WINDOW,
) -> ResearchInputs | None:
    market = db.get(Market, target.market_id)
    metric = db.get(MarketMetric, target.metric_id)
    if market is None or metric is None or metric.change_24h is None or metric.change_7d is None:
        return None
    snapshot = db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == target.market_id,
            MarketSnapshot.captured_at <= metric.computed_at,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if snapshot is None:
        return None
    outcome = db.execute(
        select(MarketOutcome).where(
            MarketOutcome.market_id == target.market_id,
            MarketOutcome.is_tracked.is_(True),
        )
    ).scalar_one_or_none()
    resolution_rule = db.execute(
        select(MarketResolutionRule)
        .where(MarketResolutionRule.market_id == target.market_id)
        .order_by(
            MarketResolutionRule.collected_at.desc(),
            MarketResolutionRule.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()
    tracked_condition = (
        resolution_rule.condition_text
        if resolution_rule is not None and resolution_rule.condition_text
        else market.title
    )
    if outcome is not None:
        tracked_condition = f"{tracked_condition} Tracked outcome: {outcome.outcome_label}."
    episode_at = _as_utc_aware(target.episode_at)
    return ResearchInputs(
        market_id=market.id,
        episode_at=episode_at,
        title=market.title,
        description=market.description or market.title,
        category=market.category,
        tracked_condition=tracked_condition,
        end_date=(
            _as_utc_aware(resolution_rule.deadline)
            if resolution_rule is not None and resolution_rule.deadline
            else _as_utc_aware(market.end_date) if market.end_date else None
        ),
        resolution_source=(
            resolution_rule.resolution_source if resolution_rule is not None else None
        ),
        resolution_exclusions=(
            list(resolution_rule.exclusions or []) if resolution_rule is not None else []
        ),
        current_value=float(snapshot.price),
        change_24h=float(metric.change_24h),
        change_7d=float(metric.change_7d),
        inflection_at=_as_utc_aware(target.inflection_at) if target.inflection_at else None,
        search_window_start=episode_at - search_window,
        search_window_end=episode_at + search_window,
        allowed_domains=(
            [urlparse(resolution_rule.resolution_source).hostname]
            if resolution_rule is not None
            and resolution_rule.resolution_source
            and urlparse(resolution_rule.resolution_source).hostname
            else []
        ),
    )


def _public_limited_decisions(
    decisions: list[VerificationDecision],
) -> list[VerificationDecision]:
    verified_seen = 0
    bounded: list[VerificationDecision] = []
    for decision in decisions:
        if decision.verification_state == "verified":
            verified_seen += 1
            if verified_seen > MAX_PUBLIC_CANDIDATES:
                decision = decision.model_copy(
                    update={
                        "verification_state": "withheld",
                        "reason_code": "public_candidate_limit",
                        "neutral_summary_ko": None,
                    }
                )
        bounded.append(decision)
    return bounded


def _source_payload(decision: VerificationDecision) -> list[dict]:
    return [source.model_dump(mode="json") for source in decision.sources]


def _persist_candidate(
    db: Session,
    *,
    target: ContextResearchTarget,
    candidate_title: str,
    candidate_event_at: datetime | None,
    decision: VerificationDecision,
    collected_at: datetime,
    expires_at: datetime,
) -> ContextCandidate:
    row = ContextCandidate(
        id=uuid.uuid4(),
        market_id=target.market_id,
        episode_at=target.episode_at,
        event_title=candidate_title,
        event_at=candidate_event_at,
        neutral_summary=decision.neutral_summary_ko or WITHHELD_SUMMARY,
        sources=_source_payload(decision),
        verification_state=decision.verification_state,
        verification_score_internal={"verified": 1.0, "withheld": 0.5, "rejected": 0.0}[
            decision.verification_state
        ],
        research_model=decision.research_model,
        verifier_model=decision.verifier_model,
        policy_version=decision.policy_version,
        evidence_hash=decision.evidence_hash,
        collected_at=collected_at,
        expires_at=expires_at,
    )
    try:
        with db.begin_nested():
            db.add(row)
            db.flush()
        return row
    except IntegrityError:
        existing = db.execute(
            select(ContextCandidate).where(
                ContextCandidate.market_id == target.market_id,
                ContextCandidate.episode_at == target.episode_at,
                ContextCandidate.evidence_hash == decision.evidence_hash,
            )
        ).scalar_one_or_none()
        if existing is None:
            raise
        return existing


def _run_log_usage(
    research: ContextResearchResult | None,
    verifier: IndependentVerifierClient,
    *,
    failed_usage: ResearchUsage | None = None,
    failed_model: str | None = None,
    failed_queries: list[str] | None = None,
    decision_counts: dict[str, int] | None = None,
    decision_reason_codes: list[str] | None = None,
) -> dict:
    usage = research.usage if research is not None else failed_usage
    research_model = research.model if research is not None else failed_model
    if usage is None:
        return {
            "verifier_model": verifier.model,
            "reported_queries": failed_queries or [],
            "decision_counts": decision_counts or {},
            "decision_reason_codes": decision_reason_codes or [],
        }
    verifier_usage = verifier.last_usage
    return {
        "research_model": research_model,
        "verifier_model": verifier.model,
        "reported_queries": research.queries if research is not None else failed_queries or [],
        "decision_counts": decision_counts or {},
        "decision_reason_codes": decision_reason_codes or [],
        "research_input_tokens": usage.input_tokens,
        "research_output_tokens": usage.output_tokens,
        "verifier_input_tokens": verifier_usage.input_tokens,
        "verifier_output_tokens": verifier_usage.output_tokens,
        "web_searches": usage.web_search_requests,
        "research_cost_usd": usage.cost_usd,
        "verifier_cost_usd": verifier_usage.cost_usd,
    }


def _record_failed_run(
    db: Session,
    target: ContextResearchTarget,
    *,
    started_at: datetime,
    finished_at: datetime,
    verifier: IndependentVerifierClient,
    research: ContextResearchResult | None,
    research_service: ContextResearchService,
    error_type: str,
) -> None:
    failed_usage = getattr(research_service, "last_usage", None)
    if not isinstance(failed_usage, ResearchUsage):
        failed_usage = None
    failed_model = getattr(research_service, "model", None)
    failed_queries = getattr(research_service, "last_queries", None)
    if not isinstance(failed_queries, list) or not all(
        isinstance(query, str) for query in failed_queries
    ):
        failed_queries = []
    reported_queries = research.queries if research is not None else failed_queries
    usage_query_count = (
        research.usage.web_search_requests
        if research is not None
        else failed_usage.web_search_requests if failed_usage is not None else 0
    )
    db.add(
        ContextCollectionRun(
            id=uuid.uuid4(),
            market_id=target.market_id,
            episode_at=target.episode_at,
            started_at=started_at,
            finished_at=finished_at,
            status="failed",
            query_count=max(usage_query_count, len(reported_queries)),
            result_count=len(research.citations) if research else 0,
            accepted_count=0,
            model_usage=_run_log_usage(
                research,
                verifier,
                failed_usage=failed_usage,
                failed_model=failed_model if isinstance(failed_model, str) else None,
                failed_queries=failed_queries,
            ),
            error_detail={"type": error_type},
        )
    )
    db.commit()


def context_spend_usd(db: Session) -> float:
    """Sum recorded research, verifier, and writer costs without DB-specific JSON SQL."""
    total = 0.0
    for usage in db.execute(select(ContextCollectionRun.model_usage)).scalars():
        if not isinstance(usage, dict):
            continue
        for key in ("research_cost_usd", "verifier_cost_usd", "writer_cost_usd"):
            value = usage.get(key)
            if isinstance(value, int | float):
                total += float(value)
    for detail in db.execute(select(DataCollectionLog.error_detail)).scalars():
        if isinstance(detail, dict):
            writer_cost = detail.get("v4_writer_cost_usd")
            if isinstance(writer_cost, int | float):
                total += float(writer_cost)
    return round(total, 8)


def _record_budget_skip(
    db: Session,
    target: ContextResearchTarget,
    *,
    at: datetime,
    verifier: IndependentVerifierClient,
    spent_usd: float,
    budget_usd: float,
) -> None:
    db.add(
        ContextCollectionRun(
            id=uuid.uuid4(),
            market_id=target.market_id,
            episode_at=target.episode_at,
            started_at=at,
            finished_at=at,
            status="partial",
            query_count=0,
            result_count=0,
            accepted_count=0,
            model_usage={
                "verifier_model": verifier.model,
                "recorded_spend_usd": spent_usd,
                "approved_budget_usd": budget_usd,
            },
            error_detail={"type": "budget_limit"},
        )
    )
    db.commit()


def run_context_research_batch(
    db: Session,
    run_timestamp: datetime,
    research_client: ContextResearchService,
    verifier: IndependentVerifierClient,
    *,
    use_latest_metrics: bool = False,
    backfill: bool = False,
    change_threshold: float = DEFAULT_CHANGE_THRESHOLD,
    staleness: timedelta = DEFAULT_STALENESS,
    budget_usd: float = APPROVED_BUDGET_USD,
    cost_reservation_usd: float = DEFAULT_COST_RESERVATION_USD,
    max_targets: int | None = None,
    target_offset: int = 0,
    clock=lambda: datetime.now(UTC),
) -> list[ContextResearchOutcome]:
    """Research, verify, and store each selected market in isolation."""
    targets = select_context_targets(
        db,
        run_timestamp,
        use_latest_metrics=use_latest_metrics,
        backfill=backfill,
        change_threshold=change_threshold,
        staleness=staleness,
    )
    offset = max(target_offset, 0)
    targets = targets[offset:]
    if max_targets is not None:
        targets = targets[: max(max_targets, 0)]
    outcomes: list[ContextResearchOutcome] = []
    for target in targets:
        started_at = clock()
        spent_usd = context_spend_usd(db)
        if spent_usd + cost_reservation_usd > min(budget_usd, APPROVED_BUDGET_USD):
            _record_budget_skip(
                db,
                target,
                at=started_at,
                verifier=verifier,
                spent_usd=spent_usd,
                budget_usd=min(budget_usd, APPROVED_BUDGET_USD),
            )
            outcomes.append(
                ContextResearchOutcome(
                    market_id=target.market_id,
                    status="skipped",
                    reason="budget_limit",
                )
            )
            continue
        research: ContextResearchResult | None = None
        try:
            inputs = build_research_inputs(db, target)
            if inputs is None:
                raise RuntimeError("Research inputs are incomplete")
            research = research_client.research(inputs)
            verification = verify_research_result(inputs, research, verifier)
            decisions = _public_limited_decisions(verification.decisions)
            decision_counts = dict(
                Counter(decision.verification_state for decision in decisions)
            )
            decision_reason_codes = sorted(
                {decision.reason_code for decision in decisions}
            )
            candidate_by_key = {
                candidate.candidate_key: candidate for candidate in research.candidates
            }
            collected_at = clock()
            expires_at = collected_at + staleness
            public_ids: list[uuid.UUID] = []
            for decision in decisions:
                candidate = candidate_by_key[decision.candidate_key]
                row = _persist_candidate(
                    db,
                    target=target,
                    candidate_title=candidate.title,
                    candidate_event_at=candidate.event_at,
                    decision=decision,
                    collected_at=collected_at,
                    expires_at=expires_at,
                )
                if row.verification_state == "verified" and row.id not in public_ids:
                    public_ids.append(row.id)

            finished_at = clock()
            status = "success" if public_ids else "no_candidate"
            db.add(
                ContextCollectionRun(
                    id=uuid.uuid4(),
                    market_id=target.market_id,
                    episode_at=target.episode_at,
                    started_at=started_at,
                    finished_at=finished_at,
                    status=status,
                    query_count=max(
                        research.usage.web_search_requests,
                        len(research.queries),
                    ),
                    result_count=len(research.citations),
                    accepted_count=len(public_ids),
                    model_usage=_run_log_usage(
                        research,
                        verifier,
                        decision_counts=decision_counts,
                        decision_reason_codes=decision_reason_codes,
                    ),
                    error_detail=None,
                )
            )
            db.commit()
            outcomes.append(
                ContextResearchOutcome(
                    market_id=target.market_id,
                    status=status,
                    accepted_count=len(public_ids),
                    candidate_ids=public_ids,
                )
            )
        except Exception as exc:
            db.rollback()
            finished_at = clock()
            try:
                _record_failed_run(
                    db,
                    target,
                    started_at=started_at,
                    finished_at=finished_at,
                    verifier=verifier,
                    research=research,
                    research_service=research_client,
                    error_type=type(exc).__name__,
                )
            except Exception:
                db.rollback()
                logger.exception("Failed to record context collection failure.")
            logger.warning(
                "Context research failed for market %s: %s",
                target.market_id,
                type(exc).__name__,
            )
            outcomes.append(
                ContextResearchOutcome(
                    market_id=target.market_id,
                    status="failed",
                    reason=type(exc).__name__,
                )
            )
    return outcomes
