"""TASK-104 on-demand request, lease, generation, cache, and failure tests."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchUsage,
)
from app.core.on_demand_briefing import (
    build_v7_input_bundle,
    claim_v7_request,
    enqueue_v7_request,
    process_v7_request,
    refresh_v7_context_for_market,
    run_pending_v7_requests,
    v7_input_fingerprint,
)
from app.db.models import (
    AiReport,
    AiReportGenerationEvent,
    AiReportGenerationRequest,
    Base,
    ContextCandidate,
    ContextCollectionRun,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketResolutionRule,
    MarketSnapshot,
)

NOW = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
    return "INTEGER"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            Market.__table__,
            MarketOutcome.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            MarketResolutionRule.__table__,
            ContextCandidate.__table__,
            ContextCollectionRun.__table__,
            AiReport.__table__,
            AiReportGenerationRequest.__table__,
            AiReportGenerationEvent.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    session.add(
        Market(
            id=MARKET_ID,
            polymarket_condition_id="condition-v7-service",
            title="정부 기관의 공식 결정 조건",
            description="공식 문서에 결정이 기록되는지를 확인하는 이슈입니다.",
            category="정치",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=30),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=30),
            last_seen_at=NOW,
        )
    )
    session.add(
        MarketResolutionRule(
            id=uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            market_id=MARKET_ID,
            condition_text="기관 공식 문서에 결정이 기록되면 조건을 충족합니다.",
            deadline=NOW + timedelta(days=30),
            exclusions=[],
            resolution_source="https://agency.gov/rule",
            source_description_hash="source-hash",
            rules_hash="rules-hash",
            collected_at=NOW - timedelta(days=1),
        )
    )
    _add_metric(session, metric_id=10, captured_at=NOW, price=0.6)
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _add_metric(db, *, metric_id: int, captured_at: datetime, price: float):
    db.add(
        MarketSnapshot(
            id=metric_id,
            market_id=MARKET_ID,
            captured_at=captured_at,
            price=price,
            volume_24h=1000,
            volume_total=10000,
            liquidity=2000,
            best_bid=None,
            best_ask=None,
        )
    )
    db.add(
        MarketMetric(
            id=metric_id,
            market_id=MARKET_ID,
            computed_at=captured_at,
            change_24h=0.02,
            change_7d=0.03,
            volatility_score=None,
            attention_score=None,
            heat_score=0.02,
            confidence_level="sufficient",
        )
    )


def _valid_output(*, metric_ref: str = "metric:10") -> str:
    return json.dumps(
        {
            "headline": "공식 결정 조건과 현재 공개 자료 요약",
            "summary": (
                "이 이슈의 공식 조건과 현재 저장된 공개 데이터가 각각 무엇을 "
                "보여주는지 근거 범위 안에서 구분해 정리합니다."
            ),
            "sections": [
                {
                    "type": "issue_overview",
                    "title": "이슈의 기준",
                    "format": "paragraph",
                    "content": (
                        "기관 공식 문서에 정해진 결정이 기록되는지가 핵심 확인 대상입니다."
                    ),
                    "items": [],
                    "evidence_refs": [
                        "market_definition:bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
                    ],
                },
                {
                    "type": "market_data",
                    "title": "저장된 공개 데이터",
                    "format": "paragraph",
                    "content": (
                        "현재 저장된 공개 데이터는 기준 시각의 관찰값과 최근 비교값을 "
                        "함께 담고 있습니다."
                    ),
                    "items": [],
                    "evidence_refs": [metric_ref],
                },
            ],
        },
        ensure_ascii=False,
    )


class FakeLLM:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def complete(self, _system, _user):
        self.calls += 1
        return self.response


def _add_context(db):
    candidate_id = uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    db.add(
        ContextCandidate(
            id=candidate_id,
            market_id=MARKET_ID,
            episode_at=NOW,
            event_title="기관 일정 공개",
            event_at=NOW - timedelta(hours=1),
            neutral_summary="기관이 공식 일정 문서를 공개했습니다.",
            sources=[
                {
                    "citation_id": "citation:official",
                    "title": "기관 공식 일정",
                    "url": "https://agency.gov/schedule",
                    "canonical_url": "https://agency.gov/schedule",
                    "domain": "agency.gov",
                    "level": "A",
                    "accepted": True,
                    "reason_code": "accepted_level_a",
                    "supported_claims": [
                        {
                            "ref": "claim:official",
                            "text": "기관이 공식 일정을 공개했습니다.",
                            "excerpt": "기관 공식 일정 문서가 공개되었습니다.",
                            "citation_id": "citation:official",
                        }
                    ],
                    "content_hash": "hash-official",
                }
            ],
            verification_state="verified",
            verification_score_internal=1.0,
            research_model="openai/research",
            verifier_model="deterministic",
            policy_version="v7-source-level-1",
            evidence_hash="v7-evidence-hash",
            collected_at=NOW,
            expires_at=NOW + timedelta(days=1),
        )
    )
    db.commit()
    return candidate_id


def test_input_fingerprint_is_stable_and_changes_with_metric_revision(db):
    first = build_v7_input_bundle(db, MARKET_ID, now=NOW)
    second = build_v7_input_bundle(db, MARKET_ID, now=NOW)
    assert first is not None and second is not None
    assert v7_input_fingerprint(first) == v7_input_fingerprint(second)

    _add_metric(db, metric_id=11, captured_at=NOW + timedelta(minutes=1), price=0.61)
    db.commit()
    changed = build_v7_input_bundle(db, MARKET_ID, now=NOW + timedelta(minutes=1))
    assert changed is not None
    assert v7_input_fingerprint(changed) != v7_input_fingerprint(first)


def test_duplicate_enqueue_joins_one_request_and_one_queue_event(db):
    first = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    second = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    assert first is not None and second is not None
    assert first.created is True
    assert second.created is False
    assert first.request_id == second.request_id
    assert db.query(AiReportGenerationRequest).count() == 1
    assert db.query(AiReportGenerationEvent).count() == 1


def test_nonexpired_lease_is_not_double_claimed_and_expired_lease_recovers(db):
    queued = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    assert queued is not None
    first = claim_v7_request(db, queued.request_id, now=NOW)
    assert first is not None and first[2] == 1
    assert claim_v7_request(db, queued.request_id, now=NOW + timedelta(minutes=1)) is None
    recovered = claim_v7_request(db, queued.request_id, now=NOW + timedelta(minutes=6))
    assert recovered is not None and recovered[2] == 2


def test_process_request_appends_v7_report_and_success_event(db):
    queued = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    assert queued is not None
    client = FakeLLM(_valid_output())
    result = process_v7_request(
        db,
        queued.request_id,
        client,
        "fake/writer",
        now=NOW + timedelta(seconds=1),
    )
    assert result.state == "succeeded"
    assert client.calls == 1
    report = db.query(AiReport).one()
    assert report.prompt_version == "v7"
    assert report.content["input_fingerprint"] == queued.input_fingerprint
    events = db.query(AiReportGenerationEvent).order_by(AiReportGenerationEvent.id).all()
    assert [event.state for event in events] == ["queued", "running", "succeeded"]


def test_unsupported_number_fails_closed_without_deleting_last_good(db):
    first = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    assert first is not None
    ok = process_v7_request(
        db,
        first.request_id,
        FakeLLM(_valid_output()),
        "fake/writer",
        now=NOW + timedelta(seconds=1),
    )
    assert ok.state == "succeeded"

    _add_metric(db, metric_id=11, captured_at=NOW + timedelta(minutes=1), price=0.61)
    db.commit()
    second = enqueue_v7_request(
        db,
        MARKET_ID,
        requested_by="user",
        now=NOW + timedelta(minutes=1),
    )
    assert second is not None
    raw = json.loads(_valid_output(metric_ref="metric:11"))
    raw["sections"][1]["content"] += " 확인되지 않은 99라는 수치를 포함합니다."
    failed = process_v7_request(
        db,
        second.request_id,
        FakeLLM(json.dumps(raw, ensure_ascii=False)),
        "fake/writer",
        now=NOW + timedelta(minutes=1, seconds=1),
    )
    assert failed.state == "failed"
    assert failed.reason_code == "unsupported_number"
    assert db.query(AiReport).count() == 1


def test_budget_reservation_blocks_before_provider_call(db):
    queued = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    assert queued is not None
    client = FakeLLM(_valid_output())
    result = process_v7_request(
        db,
        queued.request_id,
        client,
        "fake/writer",
        now=NOW + timedelta(seconds=1),
        budget_usd=0,
    )
    assert result.reason_code == "budget_limit"
    assert client.calls == 0


def test_context_refresh_with_new_evidence_creates_successor_request(db):
    queued = enqueue_v7_request(
        db,
        MARKET_ID,
        requested_by="user",
        context_refresh_requested=True,
        now=NOW,
    )
    assert queued is not None

    def refresh(session, _market_id, _now):
        _add_context(session)

    result = process_v7_request(
        db,
        queued.request_id,
        FakeLLM(_valid_output()),
        "fake/writer",
        now=NOW + timedelta(seconds=1),
        context_refresher=refresh,
    )
    assert result.state == "failed"
    assert result.reason_code == "input_changed_after_enqueue"
    assert result.successor_request_id is not None
    assert db.query(AiReportGenerationRequest).count() == 2
    assert db.query(AiReport).count() == 0


def test_v7_context_sources_keep_level_claim_and_parent_refs(db):
    candidate_id = _add_context(db)
    bundle = build_v7_input_bundle(db, MARKET_ID, now=NOW)
    assert bundle is not None
    assert bundle.context_candidate_ids == [candidate_id]
    assert bundle.sources[0].source_level == "A"
    source_item = next(item for item in bundle.writer_inputs.evidence if item.kind == "source")
    assert source_item.parent_ref == f"context:{candidate_id}"


def test_bounded_refresh_persists_v7_level_claims_and_run_audit(db):
    excerpt = "The agency publishes the documented decision and schedule."
    citation = NormalizedCitation(
        citation_id="citation:refresh",
        url="https://agency.gov/update",
        canonical_url="https://agency.gov/update",
        title="Agency documented decision",
        domain="agency.gov",
        content_excerpt=excerpt,
        content_hash=hashlib.sha256(excerpt.encode()).hexdigest(),
        retrieved_at=NOW,
    )
    result = ContextResearchResult(
        model="openai/research",
        queries=["agency documented decision"],
        citations=[citation],
        candidates=[
            ResearchCandidateDraft(
                candidate_key="candidate:refresh",
                title="Agency decision update",
                event_at=NOW,
                citation_ids=[citation.citation_id],
                matched_entities=["agency"],
                matched_condition="Agency publishes the documented decision",
                temporal_relation="same_window",
            )
        ],
        usage=ResearchUsage(input_tokens=10, output_tokens=5, web_search_requests=1),
    )

    class Research:
        model = "openai/research"

        def research(self, _inputs):
            return result

    rows = refresh_v7_context_for_market(
        db,
        MARKET_ID,
        NOW,
        research_client=Research(),
    )
    assert len(rows) == 1
    assert rows[0].verification_state == "verified"
    assert rows[0].sources[0]["level"] == "A"
    run = db.query(ContextCollectionRun).one()
    assert run.status == "success"
    assert run.accepted_count == 1


def test_standalone_worker_processes_bounded_pending_fifo(db):
    queued = enqueue_v7_request(db, MARKET_ID, requested_by="user", now=NOW)
    assert queued is not None
    client = FakeLLM(_valid_output())
    results = run_pending_v7_requests(
        db,
        client,
        "fake/writer",
        now=NOW + timedelta(seconds=1),
        max_requests=1,
    )
    assert [result.state for result in results] == ["succeeded"]
    assert client.calls == 1
    assert db.query(AiReport).count() == 1
