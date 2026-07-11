"""TASK-104 cache-backed on-demand v8 briefing service.

The scheduled collector never imports or calls this module. API and approved
development evaluation paths explicitly enqueue requests; a worker claims an
append-only lease event and appends one v8 report plus an outcome event.
"""

import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.ai_report import (
    V8_INPUT_SCHEMA_VERSION,
    V8_POLICY_VERSION,
    V8_PROMPT_VERSION,
    LLMCallError,
    LLMClient,
    V7EvidenceItem,
    V8WriterInputs,
    V8WriterOutput,
    build_caution_note,
    build_v8_prompt,
    parse_v8_writer_output,
    validate_v8_writer_output,
)
from app.core.context_policy_v7 import (
    V8_CONTEXT_POLICY_VERSION,
    ResearchClient,
    V7ConditionalVerifier,
    V7SupportedClaim,
    collect_v8_context,
)
from app.core.context_research_batch import (
    ContextResearchTarget,
    build_research_inputs,
)
from app.db.models import (
    AiReport,
    AiReportGenerationEvent,
    AiReportGenerationRequest,
    ContextCandidate,
    ContextCollectionRun,
    Market,
    MarketMetric,
    MarketResolutionRule,
    MarketSnapshot,
)

DEFAULT_LEASE_DURATION = timedelta(minutes=5)
DEFAULT_WRITER_COST_RESERVATION_USD = 0.5
DEFAULT_PROGRAM_BUDGET_USD = 100.0
V8_DATA_LIMITATIONS = (
    "공개 데이터는 전체 대중을 대표하지 않으며 저장된 근거와 기준 시각 "
    "범위에서만 읽어야 합니다."
)


class V7SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str
    context_ref: str
    citation_id: str
    title: str
    url: str
    domain: str
    source_level: Literal["A", "B", "C"]
    supported_claims: list[V7SupportedClaim] = Field(min_length=1, max_length=8)
    retrieved_at: datetime

    @model_validator(mode="after")
    def validate_exact_url_domain(self) -> "V7SourceRecord":
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("V7 source URL must be absolute HTTP(S)")
        if parsed.hostname.casefold().rstrip(".") != self.domain.casefold().rstrip("."):
            raise ValueError("V7 source URL hostname must match stored domain")
        return self


class V8StoredReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_version: Literal["v8"] = "v8"
    input_fingerprint: str = Field(min_length=64, max_length=64)
    prompt_version: Literal["v8"] = V8_PROMPT_VERSION
    policy_version: str = V8_POLICY_VERSION
    input_schema_version: str = V8_INPUT_SCHEMA_VERSION
    metric_id: int
    definition_ref: str
    context_candidate_ids: list[uuid.UUID] = Field(max_length=8)
    evidence: list[V7EvidenceItem] = Field(min_length=2, max_length=60)
    writer: V8WriterOutput
    sources: list[V7SourceRecord] = Field(max_length=24)
    data_as_of: datetime
    context_as_of: datetime | None
    data_limitations: str = Field(min_length=20, max_length=900)
    caution_note: str = Field(min_length=20, max_length=900)


class V8InputBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    writer_inputs: V8WriterInputs
    metric_id: int
    definition_ref: str
    context_candidate_ids: list[uuid.UUID]
    sources: list[V7SourceRecord]
    data_as_of: datetime
    context_as_of: datetime | None
    confidence_level: str


class EnqueueResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: uuid.UUID
    input_fingerprint: str
    created: bool
    state: Literal["queued", "running", "succeeded", "failed"]


class ProcessResult(BaseModel):
    request_id: uuid.UUID
    state: Literal["running", "succeeded", "failed", "not_claimed"]
    report_id: uuid.UUID | None = None
    reason_code: str | None = None
    successor_request_id: uuid.UUID | None = None


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _latest_metric(db: Session, market_id: uuid.UUID) -> MarketMetric | None:
    return db.execute(
        select(MarketMetric)
        .where(MarketMetric.market_id == market_id)
        .order_by(MarketMetric.computed_at.desc(), MarketMetric.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_snapshot(
    db: Session,
    market_id: uuid.UUID,
    computed_at: datetime,
) -> MarketSnapshot | None:
    return db.execute(
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_id == market_id,
            MarketSnapshot.captured_at <= computed_at,
        )
        .order_by(MarketSnapshot.captured_at.desc(), MarketSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_rule(db: Session, market_id: uuid.UUID) -> MarketResolutionRule | None:
    return db.execute(
        select(MarketResolutionRule)
        .where(MarketResolutionRule.market_id == market_id)
        .order_by(MarketResolutionRule.collected_at.desc(), MarketResolutionRule.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _v7_context_rows(
    db: Session,
    market_id: uuid.UUID,
    now: datetime,
    *,
    candidate_ids: list[uuid.UUID] | None = None,
) -> list[ContextCandidate]:
    statement = select(ContextCandidate).where(
        ContextCandidate.market_id == market_id,
        ContextCandidate.verification_state == "verified",
        ContextCandidate.policy_version.in_(
            ("v7-source-level-1", V8_CONTEXT_POLICY_VERSION)
        ),
        ContextCandidate.collected_at <= now,
        ContextCandidate.expires_at >= now,
    )
    if candidate_ids is not None:
        if not candidate_ids:
            return []
        rows = list(
            db.execute(statement.where(ContextCandidate.id.in_(candidate_ids)))
            .scalars()
            .all()
        )
        rows_by_id = {row.id: row for row in rows}
        return [
            rows_by_id[candidate_id]
            for candidate_id in candidate_ids
            if candidate_id in rows_by_id
        ]
    return list(
        db.execute(
            statement.order_by(
                ContextCandidate.collected_at.desc(), ContextCandidate.id.desc()
            ).limit(8)
        )
        .scalars()
        .all()
    )


def refresh_v8_context_for_market(
    db: Session,
    market_id: uuid.UUID,
    now: datetime,
    *,
    research_client: ResearchClient,
    verifier: V7ConditionalVerifier | None = None,
    established_domains: set[str] | None = None,
    budget_usd: float = DEFAULT_PROGRAM_BUDGET_USD,
    cost_reservation_usd: float = 2.0,
) -> list[ContextCandidate]:
    """Run one bounded v8 refresh and append candidate/run audit rows."""
    started_at = _as_utc(now)
    metric = _latest_metric(db, market_id)
    if metric is None:
        raise ValueError("latest_metric_unavailable")
    target = ContextResearchTarget(
        market_id=market_id,
        metric_id=metric.id,
        episode_at=_as_utc(metric.computed_at),
        inflection_at=None,
        reasons=("on_demand_refresh",),
    )
    inputs = build_research_inputs(db, target)
    if inputs is None:
        raise ValueError("research_inputs_unavailable")
    try:
        if _recorded_context_spend(db) + cost_reservation_usd > min(
            budget_usd, DEFAULT_PROGRAM_BUDGET_USD
        ):
            raise ValueError("context_budget_limit")
        result = collect_v8_context(
            inputs,
            research_client,
            established_domains=established_domains,
            verifier=verifier,
        )
    except Exception as exc:
        failed_usage = getattr(research_client, "last_usage", None)
        failed_queries = getattr(research_client, "last_queries", None)
        db.add(
            ContextCollectionRun(
                id=uuid.uuid4(),
                market_id=market_id,
                episode_at=target.episode_at,
                started_at=started_at,
                finished_at=started_at,
                status="failed",
                query_count=len(failed_queries) if isinstance(failed_queries, list) else 0,
                result_count=0,
                accepted_count=0,
                model_usage={
                    "policy_version": V8_CONTEXT_POLICY_VERSION,
                    "research_model": getattr(research_client, "model", None),
                    "research_input_tokens": getattr(failed_usage, "input_tokens", 0),
                    "research_output_tokens": getattr(failed_usage, "output_tokens", 0),
                    "web_searches": getattr(failed_usage, "web_search_requests", 0),
                    "research_cost_usd": getattr(failed_usage, "cost_usd", None),
                },
                error_detail={
                    "reason_code": str(exc)[:160] or type(exc).__name__,
                },
            )
        )
        db.commit()
        raise

    rows: list[ContextCandidate] = []
    for candidate in result.candidates:
        source_payload = [
            source.model_dump(mode="json") for source in candidate.sources
        ]
        canonical = json.dumps(
            {
                "candidate_key": candidate.candidate_key,
                "event_at": (
                    candidate.event_at.isoformat()
                    if isinstance(candidate.event_at, datetime)
                    else None
                ),
                "sources": source_payload,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        state = {
            "accepted": "verified",
            "withheld": "withheld",
            "rejected": "rejected",
        }[candidate.state]
        row = ContextCandidate(
            id=uuid.uuid4(),
            market_id=market_id,
            episode_at=target.episode_at,
            event_title=candidate.title,
            event_at=candidate.event_at,
            neutral_summary=(
                candidate.matched_condition
                if candidate.state == "accepted"
                else "공개 기준을 충족하지 않아 브리핑 근거에서 제외된 자료입니다."
            ),
            sources=source_payload,
            verification_state=state,
            verification_score_internal={"verified": 1.0, "withheld": 0.5, "rejected": 0.0}[
                state
            ],
            research_model=result.research_model,
            verifier_model=(
                verifier.model
                if candidate.verifier_triggers and verifier is not None
                else "deterministic"
            ),
            policy_version=result.policy_version,
            evidence_hash=hashlib.sha256(canonical.encode()).hexdigest(),
            collected_at=started_at,
            expires_at=started_at + timedelta(hours=24),
        )
        try:
            with db.begin_nested():
                db.add(row)
                db.flush()
            rows.append(row)
        except IntegrityError:
            continue

    accepted_count = sum(row.verification_state == "verified" for row in rows)
    usage = result.usage
    db.add(
        ContextCollectionRun(
            id=uuid.uuid4(),
            market_id=market_id,
            episode_at=target.episode_at,
            started_at=started_at,
            finished_at=started_at,
            status="success" if accepted_count else "no_candidate",
            query_count=len(result.queries),
            result_count=len(result.candidates),
            accepted_count=accepted_count,
            model_usage={
                "policy_version": result.policy_version,
                "research_model": result.research_model,
                "verifier_model": verifier.model if verifier is not None else None,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "web_searches": usage.web_search_requests,
                "cost_usd": usage.cost_usd,
                "research_cost_usd": usage.cost_usd,
            },
            error_detail=None,
        )
    )
    db.commit()
    return rows


# Historical import compatibility; active v8 callers use the name above.
refresh_v7_context_for_market = refresh_v8_context_for_market


def _recorded_context_spend(db: Session) -> float:
    """Sum context costs from the append-only context run audit."""
    total = 0.0
    for usage in db.execute(select(ContextCollectionRun.model_usage)).scalars():
        if not isinstance(usage, dict):
            continue
        values = [
            usage.get("research_cost_usd", usage.get("cost_usd")),
            usage.get("verifier_cost_usd"),
        ]
        total += sum(float(value) for value in values if isinstance(value, int | float))
    return round(total, 8)


def _source_evidence(
    row: ContextCandidate,
) -> tuple[list[V7EvidenceItem], list[V7SourceRecord]]:
    context_ref = f"context:{row.id}"
    evidence: list[V7EvidenceItem] = []
    records: list[V7SourceRecord] = []
    for index, raw in enumerate(row.sources or []):
        if not isinstance(raw, dict):
            continue
        level = raw.get("level") or raw.get("source_level")
        claims = raw.get("supported_claims")
        if level not in {"A", "B", "C"} or not isinstance(claims, list) or not claims:
            continue
        citation_id = str(raw.get("citation_id") or "").strip()
        title = str(raw.get("title") or "").strip()
        url = str(raw.get("url") or "").strip()
        domain = str(raw.get("domain") or "").strip().casefold()
        if not citation_id or not title or not url or not domain:
            continue
        suffix = hashlib.sha256(f"{row.id}:{citation_id}:{index}".encode()).hexdigest()[:20]
        source_ref = f"source:{suffix}"
        source_text = json.dumps(
            {
                "title": title,
                "domain": domain,
                "source_level": level,
                "supported_claims": claims,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        evidence.append(
            V7EvidenceItem(
                ref=source_ref,
                kind="source",
                text=source_text,
                parent_ref=context_ref,
                source_level=level,
            )
        )
        records.append(
            V7SourceRecord(
                id=source_ref,
                context_ref=context_ref,
                citation_id=citation_id,
                title=title,
                url=url,
                domain=domain,
                source_level=level,
                supported_claims=claims,
                retrieved_at=_as_utc(row.collected_at),
            )
        )
    return evidence, records


def build_v8_input_bundle(
    db: Session,
    market_id: uuid.UUID,
    *,
    now: datetime,
    metric_id: int | None = None,
    context_candidate_ids: list[uuid.UUID] | None = None,
    definition_ref: str | None = None,
) -> V8InputBundle | None:
    """Reconstruct one exact v8 writer/evidence input from stored rows."""
    market = db.get(Market, market_id)
    metric = (
        db.get(MarketMetric, metric_id)
        if metric_id is not None
        else _latest_metric(db, market_id)
    )
    if market is None or metric is None:
        return None
    if metric.market_id != market_id:
        return None
    snapshot = _latest_snapshot(db, market_id, metric.computed_at)
    if snapshot is None:
        return None
    if definition_ref is None:
        rule = _latest_rule(db, market_id)
        resolved_definition_ref = (
            f"market_definition:{rule.id}"
            if rule is not None
            else f"market_definition:market-{market.id}"
        )
    elif definition_ref == f"market_definition:market-{market.id}":
        rule = None
        resolved_definition_ref = definition_ref
    else:
        try:
            rule_id = uuid.UUID(definition_ref.removeprefix("market_definition:"))
        except ValueError:
            return None
        rule = db.get(MarketResolutionRule, rule_id)
        if rule is None or rule.market_id != market_id:
            return None
        resolved_definition_ref = definition_ref
    definition_text = (
        rule.condition_text
        if rule is not None and rule.condition_text
        else market.description or market.title
    )
    evidence = [
        V7EvidenceItem(
            ref=resolved_definition_ref,
            kind="market_definition",
            text=definition_text,
        ),
        V7EvidenceItem(
            ref=f"metric:{metric.id}",
            kind="metric",
            text=json.dumps(
                {
                    "data_as_of": _as_utc(snapshot.captured_at).isoformat(),
                    "comparison_window_24h_hours": 24,
                    "comparison_window_7d_days": 7,
                    "current_value": float(snapshot.price),
                    "current_value_percent": round(float(snapshot.price) * 100, 6),
                    "change_24h": (
                        float(metric.change_24h) if metric.change_24h is not None else None
                    ),
                    "change_24h_pp": (
                        round(float(metric.change_24h) * 100, 6)
                        if metric.change_24h is not None
                        else None
                    ),
                    "change_7d": (
                        float(metric.change_7d) if metric.change_7d is not None else None
                    ),
                    "change_7d_pp": (
                        round(float(metric.change_7d) * 100, 6)
                        if metric.change_7d is not None
                        else None
                    ),
                    "confidence_level": metric.confidence_level,
                },
                sort_keys=True,
            ),
        ),
    ]
    limitation_ref = f"data_limitation:{metric.confidence_level}"
    evidence.append(
        V7EvidenceItem(
            ref=limitation_ref,
            kind="data_limitation",
            text=(
                "공개 데이터는 전체 대중을 대표하지 않으며 활동량, 유동성, "
                "비교 이력에 따라 해석 범위가 달라질 수 있습니다."
            ),
        )
    )

    context_ids: list[uuid.UUID] = []
    source_records: list[V7SourceRecord] = []
    context_times: list[datetime] = []
    rows = _v7_context_rows(
        db,
        market_id,
        now,
        candidate_ids=context_candidate_ids,
    )
    if context_candidate_ids is not None and len(rows) != len(context_candidate_ids):
        return None
    for row in rows:
        context_ref = f"context:{row.id}"
        source_evidence, records = _source_evidence(row)
        if not records:
            continue
        evidence.append(
            V7EvidenceItem(
                ref=context_ref,
                kind="context",
                text=row.neutral_summary,
            )
        )
        evidence.extend(source_evidence)
        source_records.extend(records)
        context_ids.append(row.id)
        context_times.append(_as_utc(row.collected_at))

    try:
        writer_inputs = V8WriterInputs(
            issue_id=market.id,
            title=market.title,
            category=market.category,
            evidence=evidence,
        )
    except ValidationError:
        return None
    return V8InputBundle(
        writer_inputs=writer_inputs,
        metric_id=metric.id,
        definition_ref=resolved_definition_ref,
        context_candidate_ids=context_ids,
        sources=source_records,
        data_as_of=_as_utc(snapshot.captured_at),
        context_as_of=max(context_times) if context_times else None,
        confidence_level=metric.confidence_level,
    )


def v8_input_fingerprint(bundle: V8InputBundle) -> str:
    canonical = {
        "issue_id": str(bundle.writer_inputs.issue_id),
        "metric_id": bundle.metric_id,
        "definition_ref": bundle.definition_ref,
        "context_candidate_ids": [str(value) for value in bundle.context_candidate_ids],
        "evidence": [item.model_dump(mode="json") for item in bundle.writer_inputs.evidence],
        "prompt_version": V8_PROMPT_VERSION,
        "policy_version": V8_POLICY_VERSION,
        "context_policy_version": V8_CONTEXT_POLICY_VERSION,
        "input_schema_version": V8_INPUT_SCHEMA_VERSION,
    }
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def latest_request_event(
    db: Session,
    request_id: uuid.UUID,
) -> AiReportGenerationEvent | None:
    return db.execute(
        select(AiReportGenerationEvent)
        .where(AiReportGenerationEvent.request_id == request_id)
        .order_by(
            AiReportGenerationEvent.recorded_at.desc(),
            AiReportGenerationEvent.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def _append_event(
    db: Session,
    request_id: uuid.UUID,
    state: Literal["queued", "running", "succeeded", "failed"],
    *,
    attempt_number: int,
    now: datetime,
    lease_token: uuid.UUID | None = None,
    lease_expires_at: datetime | None = None,
    report_id: uuid.UUID | None = None,
    error_code: str | None = None,
    usage: dict | None = None,
) -> AiReportGenerationEvent:
    event = AiReportGenerationEvent(
        request_id=request_id,
        state=state,
        attempt_number=attempt_number,
        recorded_at=now,
        lease_token=lease_token,
        lease_expires_at=lease_expires_at,
        report_id=report_id,
        error_code=error_code,
        usage=usage or {},
    )
    db.add(event)
    db.flush()
    return event


def enqueue_v8_request(
    db: Session,
    market_id: uuid.UUID,
    *,
    requested_by: Literal["user", "development_evaluation"],
    context_refresh_requested: bool = False,
    now: datetime | None = None,
) -> EnqueueResult | None:
    """Create or join exactly one immutable market/fingerprint request."""
    requested_at = _as_utc(now or datetime.now(UTC))
    bundle = build_v8_input_bundle(db, market_id, now=requested_at)
    if bundle is None:
        return None
    fingerprint = v8_input_fingerprint(bundle)
    existing = db.execute(
        select(AiReportGenerationRequest).where(
            AiReportGenerationRequest.market_id == market_id,
            AiReportGenerationRequest.input_fingerprint == fingerprint,
        )
    ).scalar_one_or_none()
    if existing is not None:
        latest = latest_request_event(db, existing.id)
        state = latest.state if latest is not None else "queued"
        if state == "failed":
            _append_event(
                db,
                existing.id,
                "queued",
                attempt_number=latest.attempt_number,
                now=requested_at,
            )
            db.commit()
            state = "queued"
        return EnqueueResult(
            request_id=existing.id,
            input_fingerprint=fingerprint,
            created=False,
            state=state,
        )

    request = AiReportGenerationRequest(
        id=uuid.uuid4(),
        market_id=market_id,
        input_fingerprint=fingerprint,
        prompt_version=V8_PROMPT_VERSION,
        policy_version=V8_POLICY_VERSION,
        input_schema_version=V8_INPUT_SCHEMA_VERSION,
        requested_by=requested_by,
        context_refresh_requested=context_refresh_requested,
        input_evidence_refs=[item.ref for item in bundle.writer_inputs.evidence],
        requested_at=requested_at,
    )
    try:
        db.add(request)
        db.flush([request])
        _append_event(db, request.id, "queued", attempt_number=0, now=requested_at)
        db.commit()
        return EnqueueResult(
            request_id=request.id,
            input_fingerprint=fingerprint,
            created=True,
            state="queued",
        )
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(AiReportGenerationRequest).where(
                AiReportGenerationRequest.market_id == market_id,
                AiReportGenerationRequest.input_fingerprint == fingerprint,
            )
        ).scalar_one()
        latest = latest_request_event(db, existing.id)
        return EnqueueResult(
            request_id=existing.id,
            input_fingerprint=fingerprint,
            created=False,
            state=latest.state if latest is not None else "queued",
        )


def claim_v8_request(
    db: Session,
    request_id: uuid.UUID,
    *,
    now: datetime | None = None,
    lease_duration: timedelta = DEFAULT_LEASE_DURATION,
) -> tuple[AiReportGenerationRequest, uuid.UUID, int] | None:
    """Append a running lease when queued or when the latest lease expired."""
    claimed_at = _as_utc(now or datetime.now(UTC))
    request = db.execute(
        select(AiReportGenerationRequest)
        .where(AiReportGenerationRequest.id == request_id)
        .with_for_update()
    ).scalar_one_or_none()
    if request is None:
        return None
    if request.prompt_version != V8_PROMPT_VERSION:
        return None
    latest = latest_request_event(db, request_id)
    if latest is None or latest.state in {"succeeded", "failed"}:
        return None
    if (
        latest.state == "running"
        and latest.lease_expires_at is not None
        and _as_utc(latest.lease_expires_at) > claimed_at
    ):
        return None
    attempt = max(1, latest.attempt_number + 1)
    token = uuid.uuid4()
    _append_event(
        db,
        request_id,
        "running",
        attempt_number=attempt,
        now=claimed_at,
        lease_token=token,
        lease_expires_at=claimed_at + lease_duration,
    )
    db.commit()
    return request, token, attempt


def _recorded_writer_spend(db: Session) -> float:
    rows = db.execute(select(AiReportGenerationEvent.usage)).scalars().all()
    total = 0.0
    for usage in rows:
        if isinstance(usage, dict) and isinstance(usage.get("writer_cost_usd"), int | float):
            total += float(usage["writer_cost_usd"])
    return round(total, 8)


def _writer_usage(client: LLMClient, start_index: int) -> dict:
    records = getattr(client, "usage_records", None)
    if not isinstance(records, list):
        return {}
    recent = records[start_index:]
    costs = [record.cost_usd for record in recent if record.cost_usd is not None]
    return {
        "writer_input_tokens": sum(record.input_tokens for record in recent),
        "writer_output_tokens": sum(record.output_tokens for record in recent),
        "writer_cost_usd": round(sum(costs), 8) if costs else None,
    }


def reconstruct_v8_report(
    db: Session,
    report: AiReport,
) -> V8StoredReportPayload:
    """Rebuild and validate one stored v8 report against generation-time rows."""
    if report.status != "success" or report.prompt_version != V8_PROMPT_VERSION:
        raise ValueError("not_a_successful_v8_report")
    try:
        payload = V8StoredReportPayload.model_validate(report.content)
    except ValidationError as exc:
        raise ValueError("invalid_v8_stored_payload") from exc
    if report.input_metrics_id != payload.metric_id:
        raise ValueError("v8_metric_id_mismatch")
    generated_at = _as_utc(report.generated_at)
    bundle = build_v8_input_bundle(
        db,
        report.market_id,
        now=generated_at,
        metric_id=payload.metric_id,
        context_candidate_ids=payload.context_candidate_ids,
        definition_ref=payload.definition_ref,
    )
    if bundle is None:
        raise ValueError("v8_evidence_bundle_unavailable")
    if v8_input_fingerprint(bundle) != payload.input_fingerprint:
        raise ValueError("v8_input_fingerprint_mismatch")
    if payload.definition_ref != bundle.definition_ref:
        raise ValueError("v8_definition_ref_mismatch")
    if payload.evidence != bundle.writer_inputs.evidence:
        raise ValueError("v8_evidence_snapshot_mismatch")
    if payload.sources != bundle.sources:
        raise ValueError("v8_source_snapshot_mismatch")
    if payload.data_as_of != bundle.data_as_of or payload.context_as_of != bundle.context_as_of:
        raise ValueError("v8_evidence_timestamp_mismatch")
    if payload.data_as_of > generated_at or (
        payload.context_as_of is not None and payload.context_as_of > generated_at
    ):
        raise ValueError("v8_evidence_after_generation")
    validation = validate_v8_writer_output(payload.writer, bundle.writer_inputs)
    if not validation.passed:
        raise ValueError(f"v8_writer_validation_failed:{validation.rule}")
    if payload.data_limitations != V8_DATA_LIMITATIONS:
        raise ValueError("v8_data_limitations_mismatch")
    if payload.caution_note != build_caution_note(bundle.confidence_level):
        raise ValueError("v8_caution_mismatch")
    return payload


def _fail_request(
    db: Session,
    request_id: uuid.UUID,
    *,
    attempt: int,
    now: datetime,
    error_code: str,
    usage: dict | None = None,
) -> ProcessResult:
    _append_event(
        db,
        request_id,
        "failed",
        attempt_number=attempt,
        now=now,
        error_code=error_code,
        usage=usage,
    )
    db.commit()
    return ProcessResult(request_id=request_id, state="failed", reason_code=error_code)


def process_v8_request(
    db: Session,
    request_id: uuid.UUID,
    llm_client: LLMClient,
    model_name: str,
    *,
    now: datetime | None = None,
    budget_usd: float = DEFAULT_PROGRAM_BUDGET_USD,
    writer_cost_reservation_usd: float = DEFAULT_WRITER_COST_RESERVATION_USD,
    context_refresher: Callable[[Session, uuid.UUID, datetime], None] | None = None,
) -> ProcessResult:
    """Claim, optionally refresh context, generate once, validate, and append."""
    processed_at = _as_utc(now or datetime.now(UTC))
    claimed = claim_v8_request(db, request_id, now=processed_at)
    if claimed is None:
        return ProcessResult(request_id=request_id, state="not_claimed")
    request, _lease_token, attempt = claimed

    if request.context_refresh_requested:
        if context_refresher is None:
            return _fail_request(
                db,
                request_id,
                attempt=attempt,
                now=processed_at,
                error_code="context_refresher_unavailable",
            )
        try:
            context_refresher(db, request.market_id, processed_at)
        except Exception:
            db.rollback()
            return _fail_request(
                db,
                request_id,
                attempt=attempt,
                now=processed_at,
                error_code="context_refresh_failed",
            )

    bundle = build_v8_input_bundle(db, request.market_id, now=processed_at)
    if bundle is None:
        return _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code="input_bundle_unavailable",
        )
    current_fingerprint = v8_input_fingerprint(bundle)
    if current_fingerprint != request.input_fingerprint:
        successor = enqueue_v8_request(
            db,
            request.market_id,
            requested_by=request.requested_by,
            context_refresh_requested=False,
            now=processed_at + timedelta(microseconds=1),
        )
        result = _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code="input_changed_after_enqueue",
            usage={
                "successor_request_id": str(successor.request_id) if successor else None,
            },
        )
        return result.model_copy(
            update={"successor_request_id": successor.request_id if successor else None}
        )
    if _recorded_writer_spend(db) + writer_cost_reservation_usd > min(
        budget_usd, DEFAULT_PROGRAM_BUDGET_USD
    ):
        return _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code="budget_limit",
        )

    system_prompt, user_prompt = build_v8_prompt(bundle.writer_inputs)
    usage_records = getattr(llm_client, "usage_records", None)
    usage_start = len(usage_records) if isinstance(usage_records, list) else 0
    try:
        raw = llm_client.complete(system_prompt, user_prompt)
    except LLMCallError:
        return _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code="writer_provider_failure",
            usage=_writer_usage(llm_client, usage_start),
        )
    usage = _writer_usage(llm_client, usage_start)
    output = parse_v8_writer_output(raw)
    if output is None:
        return _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code="writer_schema_failure",
            usage=usage,
        )
    validation = validate_v8_writer_output(output, bundle.writer_inputs)
    if not validation.passed:
        return _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code=validation.rule or "writer_validation_failure",
            usage=usage,
        )

    caution = build_caution_note(bundle.confidence_level)
    if caution is None:
        return _fail_request(
            db,
            request_id,
            attempt=attempt,
            now=processed_at,
            error_code="unknown_confidence_level",
            usage=usage,
        )
    payload = V8StoredReportPayload(
        input_fingerprint=request.input_fingerprint,
        metric_id=bundle.metric_id,
        definition_ref=bundle.definition_ref,
        context_candidate_ids=bundle.context_candidate_ids,
        evidence=bundle.writer_inputs.evidence,
        writer=output,
        sources=bundle.sources,
        data_as_of=bundle.data_as_of,
        context_as_of=bundle.context_as_of,
        data_limitations=V8_DATA_LIMITATIONS,
        caution_note=caution,
    )
    report = AiReport(
        id=uuid.uuid4(),
        market_id=request.market_id,
        generated_at=processed_at,
        input_metrics_id=bundle.metric_id,
        content=payload.model_dump(mode="json"),
        model_used=model_name,
        prompt_version=V8_PROMPT_VERSION,
        status="success",
    )
    db.add(report)
    db.flush([report])
    _append_event(
        db,
        request_id,
        "succeeded",
        attempt_number=attempt,
        now=processed_at + timedelta(microseconds=1),
        report_id=report.id,
        usage=usage,
    )
    db.commit()
    return ProcessResult(
        request_id=request_id,
        state="succeeded",
        report_id=report.id,
    )


def pending_v8_request_ids(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = 10,
) -> list[uuid.UUID]:
    """Return queued or expired-running requests in deterministic FIFO order."""
    reference = _as_utc(now or datetime.now(UTC))
    requests = list(
        db.execute(
            select(AiReportGenerationRequest)
            .where(AiReportGenerationRequest.prompt_version == V8_PROMPT_VERSION)
            .order_by(
                AiReportGenerationRequest.requested_at.asc(),
                AiReportGenerationRequest.id.asc(),
            )
        )
        .scalars()
        .all()
    )
    pending: list[uuid.UUID] = []
    for request in requests:
        latest = latest_request_event(db, request.id)
        if latest is None or latest.state == "queued":
            pending.append(request.id)
        elif (
            latest.state == "running"
            and latest.lease_expires_at is not None
            and _as_utc(latest.lease_expires_at) <= reference
        ):
            pending.append(request.id)
        if len(pending) >= min(max(limit, 1), 50):
            break
    return pending


def run_pending_v8_requests(
    db: Session,
    llm_client: LLMClient,
    model_name: str,
    *,
    now: datetime | None = None,
    max_requests: int = 10,
    context_refresher: Callable[[Session, uuid.UUID, datetime], None] | None = None,
) -> list[ProcessResult]:
    """Process a bounded FIFO slice for a standalone recoverable worker."""
    reference = _as_utc(now or datetime.now(UTC))
    return [
        process_v8_request(
            db,
            request_id,
            llm_client,
            model_name,
            now=reference + timedelta(microseconds=index),
            context_refresher=context_refresher,
        )
        for index, request_id in enumerate(
            pending_v8_request_ids(db, now=reference, limit=max_requests)
        )
    ]
