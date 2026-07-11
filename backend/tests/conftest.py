"""Shared test fixtures.

Registers a SQLite-compatible compile rule for the Postgres-only JSONB
column type so backend/app/db/models.py's DDL can be created against an
in-memory SQLite DB for tests. This is a local/dev-only test fixture per
TASK-010's constraint against applying migrations.py/001_initial_schema.sql
to any shared or production database - the override only affects the
"sqlite" dialect used here and never touches the real Postgres path.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import categories as categories_routes
from app.api.routes import issues as issues_routes
from app.core.ai_report import (
    ResolutionRulesInput,
    V4ContextSource,
    V4LLMFields,
    V4ReportInputs,
    V4VerifiedCandidateInput,
    V5LLMFields,
    assemble_v4_report_content,
    assemble_v5_report_content,
    build_v4_stored_payload,
    build_v5_stored_payload,
    build_v6_stored_payload,
    determine_v6_report_mode,
    parse_v6_briefing,
)
from app.db.models import (
    AiReport,
    AiReportGenerationBlock,
    AiReportGenerationEvent,
    AiReportGenerationRequest,
    Base,
    ContextCandidate,
    ContextCollectionRun,
    DataCollectionLog,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketResolutionRule,
    MarketSnapshot,
    RelatedEvent,
)
from app.main import app

NOW = datetime(2026, 7, 8, 9, 0, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
MARKET_ID_NO_METRIC = uuid.UUID("22222222-2222-4222-8222-222222222222")
REPORT_ID_OLD = uuid.UUID("33333333-3333-4333-8333-333333333333")
REPORT_ID_LATEST = uuid.UUID("44444444-4444-4444-8444-444444444444")
REPORT_ID_FAILED = uuid.UUID("55555555-5555-4555-8555-555555555555")
CONTEXT_CANDIDATE_ID = uuid.UUID("66666666-6666-4666-8666-666666666666")


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
    return "INTEGER"


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    # Force explicit TEXT affinity. Without this, SQLAlchemy's generic
    # fallback DDL for postgresql.UUID doesn't contain a CHAR/TEXT/CLOB
    # keyword, so SQLite gives it NUMERIC affinity - a value that happens to
    # be an all-digit hex string (e.g. a UUID with no a-f characters) then
    # round-trips back as a lossy float instead of the original UUID.
    return "CHAR(32)"


@pytest.fixture
def db_session():
    # StaticPool + check_same_thread=False: TestClient dispatches sync route
    # handlers onto a worker thread, but a plain sqlite3 ":memory:" connection
    # is thread-affine and each new connection is otherwise a *separate* empty
    # DB, so the pool must share the single connection across threads.
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
            MarketResolutionRule.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            IssueSignal.__table__,
            AiReport.__table__,
            AiReportGenerationRequest.__table__,
            AiReportGenerationEvent.__table__,
            AiReportGenerationBlock.__table__,
            ContextCandidate.__table__,
            ContextCollectionRun.__table__,
            DataCollectionLog.__table__,
            RelatedEvent.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def live_client(db_session):
    def override():
        yield db_session

    app.dependency_overrides[categories_routes._get_optional_db] = override
    app.dependency_overrides[issues_routes._get_optional_db] = override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def seed_basic_market(db_session) -> None:
    """One market with snapshot + metric + tracked outcome + signal."""
    db_session.add(
        Market(
            id=MARKET_ID,
            polymarket_condition_id="cond-1",
            title="Will Test issue resolve Yes?",
            description="A seeded test issue.",
            category="technology",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=30),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=30),
            last_seen_at=NOW,
        )
    )
    db_session.add(
        MarketOutcome(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            outcome_label="Yes",
            token_id="token-1",
            is_tracked=True,
        )
    )
    db_session.add(
        MarketSnapshot(
            id=1,  # BigInteger PK: SQLite won't autoincrement it like Postgres BIGSERIAL does
            market_id=MARKET_ID,
            captured_at=NOW,
            price=0.63,
            volume_24h=1000,
            volume_total=50000,
            liquidity=2000,
            best_bid=0.62,
            best_ask=0.64,
        )
    )
    db_session.add(
        MarketMetric(
            id=1,
            market_id=MARKET_ID,
            computed_at=NOW,
            change_24h=0.08,
            change_7d=0.11,
            volatility_score=0.2,
            attention_score=0.5,
            heat_score=78.4,
            confidence_level="sufficient",
        )
    )
    db_session.add(
        IssueSignal(
            id=1,
            market_id=MARKET_ID,
            signal_type="expectation_shift",
            severity="medium",
            window="24h",
            magnitude=0.08,
            triggered_at=NOW,
            detail=None,
        )
    )
    db_session.add(
        RelatedEvent(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            event_title="A related context event",
            event_date=NOW - timedelta(days=1),
            note="A related event candidate, not a cause: context only.",
        )
    )
    db_session.commit()


def seed_market_without_metric(db_session) -> None:
    """One market with a snapshot + tracked outcome but no metric row yet -
    exercises the insufficient_data / null-fields path."""
    db_session.add(
        Market(
            id=MARKET_ID_NO_METRIC,
            polymarket_condition_id="cond-2",
            title="A brand new market with no metrics computed yet",
            description=None,
            category="economy",
            outcome_type="binary",
            status="active",
            market_created_at=NOW,
            end_date=NOW + timedelta(days=90),
            first_seen_at=NOW,
            last_seen_at=NOW,
        )
    )
    db_session.add(
        MarketOutcome(
            id=uuid.uuid4(),
            market_id=MARKET_ID_NO_METRIC,
            outcome_label="Yes",
            token_id="token-2",
            is_tracked=True,
        )
    )
    db_session.add(
        MarketSnapshot(
            id=2,
            market_id=MARKET_ID_NO_METRIC,
            captured_at=NOW,
            price=0.5,
            volume_24h=None,
            volume_total=None,
            liquidity=None,
            best_bid=None,
            best_ask=None,
        )
    )
    db_session.commit()


def report_content(label: str) -> dict[str, str | None]:
    return {
        "issue_overview": (
            f"{label} issue overview from stored data that explains the tracked condition."
        ),
        "current_data_reading": (
            f"{label} current data reading tracks expectation value based on "
            "public participant dataset."
        ),
        "possible_outlook": (
            f"{label} possible outlook describes conditional later readings "
            "without asserting a real-world forecast."
        ),
        "possible_drivers": (
            f"{label} possible drivers lists manually reviewed factor candidates "
            "for comparison alongside the movement."
        ),
        "external_context": (
            f"{label} external context narrative for manually reviewed context candidate."
        ),
        "what_to_check": f"{label} what to check lists verification items and dates.",
        "data_limitations": (
            f"{label} data limitations details activity level, liquidity depth, "
            "volatility, and representativeness constraints."
        ),
        "caution_note": (
            f"{label} caution note includes participant scope, no-outcome claims, "
            "representativeness limitations, and independent verification requirement."
        ),
    }


def seed_ai_report(
    db_session,
    *,
    report_id: uuid.UUID = REPORT_ID_LATEST,
    market_id: uuid.UUID = MARKET_ID,
    generated_at: datetime = NOW,
    input_metrics_id: int | None = 1,
    status: str = "success",
    label: str = "latest",
    prompt_version: str = "v3",
) -> None:
    db_session.add(
        AiReport(
            id=report_id,
            market_id=market_id,
            generated_at=generated_at,
            input_metrics_id=input_metrics_id,
            content=report_content(label),
            model_used="template-v1",
            prompt_version=prompt_version,
            status=status,
        )
    )
    db_session.commit()


def seed_v4_report(
    db_session,
    *,
    report_id: uuid.UUID = REPORT_ID_LATEST,
    generated_at: datetime = NOW + timedelta(minutes=5),
    with_candidate: bool = True,
    status: str = "success",
) -> tuple[AiReport, ContextCandidate | None]:
    """Seed one internally valid v4 evidence envelope for API tests."""
    candidate = None
    candidate_inputs: list[V4VerifiedCandidateInput] = []
    if with_candidate:
        source = V4ContextSource(
            citation_id="citation:official",
            title="Official context notice",
            url="https://example.gov/notices/context",
            canonical_url="https://example.gov/notices/context",
            domain="example.gov",
            source_type="official",
            content_hash="a" * 64,
        )
        candidate = ContextCandidate(
            id=CONTEXT_CANDIDATE_ID,
            market_id=MARKET_ID,
            episode_at=NOW,
            event_title="Official context notice was published",
            event_at=NOW - timedelta(minutes=30),
            neutral_summary="공식 공개 자료에 검토 구간의 관련 공지가 기록되었습니다.",
            sources=[source.model_dump(mode="json")],
            verification_state="verified",
            verification_score_internal=1,
            research_model="research/model",
            verifier_model="verifier/model",
            policy_version="v4",
            evidence_hash="b" * 64,
            collected_at=NOW,
            expires_at=NOW + timedelta(hours=24),
        )
        db_session.add(candidate)
        candidate_inputs.append(
            V4VerifiedCandidateInput(
                id=candidate.id,
                title=candidate.event_title,
                event_at=candidate.event_at,
                neutral_summary=candidate.neutral_summary,
                sources=[source],
            )
        )

    inputs = V4ReportInputs(
        market_id=MARKET_ID,
        metric_id=1,
        episode_at=NOW,
        data_as_of=NOW,
        title="Will Test issue resolve Yes?",
        description="A seeded test issue.",
        category="technology",
        outcome_label="Yes",
        end_date=NOW + timedelta(days=30),
        current_value=0.63,
        change_24h=0.08,
        change_7d=0.11,
        confidence_level="sufficient",
        volume_24h=1000,
        liquidity=2000,
        context_candidates=candidate_inputs,
        resolution_rules=ResolutionRulesInput(
            condition_text="The documented test condition is recorded by the deadline.",
            deadline=NOW + timedelta(days=30),
            exclusions=[],
            resolution_source=None,
            source_description_hash="test-description-hash",
            rules_hash="test-rules-hash",
            collected_at=NOW - timedelta(minutes=10),
        ),
    )
    fields = V4LLMFields(
        issue_overview=(
            "이 이슈는 공개 문서에 적힌 조건의 충족 여부를 정해진 기한 기준으로 추적합니다."
        ),
        what_to_check=(
            "게시된 조건 문구와 기준 시각 이후 공개 자료의 갱신 내용을 추가로 확인해야 합니다."
        ),
    )
    content = assemble_v4_report_content(inputs, fields)
    assert content is not None
    payload = build_v4_stored_payload(inputs, content)
    report = AiReport(
        id=report_id,
        market_id=MARKET_ID,
        generated_at=generated_at,
        input_metrics_id=1,
        content=payload.model_dump(mode="json"),
        model_used="writer/model",
        prompt_version="v4",
        status=status,
    )
    db_session.add(report)
    db_session.commit()
    return report, candidate


def seed_v5_report(
    db_session,
    *,
    report_id: uuid.UUID = REPORT_ID_LATEST,
    generated_at: datetime = NOW + timedelta(minutes=5),
    with_candidate: bool = True,
) -> tuple[AiReport, ContextCandidate | None]:
    report, candidate = seed_v4_report(
        db_session,
        report_id=report_id,
        generated_at=generated_at,
        with_candidate=with_candidate,
    )
    candidate_inputs = []
    if candidate is not None:
        candidate_inputs = [
            V4VerifiedCandidateInput(
                id=candidate.id,
                title=candidate.event_title,
                event_at=candidate.event_at,
                neutral_summary=candidate.neutral_summary,
                sources=[V4ContextSource.model_validate(source) for source in candidate.sources],
            )
        ]
    inputs = V4ReportInputs(
        market_id=MARKET_ID,
        metric_id=1,
        episode_at=NOW,
        data_as_of=NOW,
        title="Will the test issue resolve Yes?",
        description="A seeded test issue.",
        category="technology",
        outcome_label="Yes",
        end_date=NOW + timedelta(days=30),
        current_value=0.63,
        change_24h=0.08,
        change_7d=0.11,
        confidence_level="sufficient",
        volume_24h=1000,
        liquidity=2000,
        context_candidates=candidate_inputs,
        resolution_rules=ResolutionRulesInput(
            condition_text="The documented test condition is recorded by the deadline.",
            deadline=NOW + timedelta(days=30),
            exclusions=[],
            resolution_source=None,
            source_description_hash="test-description-hash",
            rules_hash="test-rules-hash",
            collected_at=NOW - timedelta(minutes=10),
        ),
    )
    fields = V5LLMFields(
        executive_summary=(
            "Will the test issue resolve Yes? 질문이 정해진 기준일까지 문서 조건을 "
            "충족하는지 다루는 이슈입니다. "
            "현재 공개 데이터와 최근 움직임은 현실의 결과를 뜻하지 않습니다."
        ),
        current_data_interpretation=(
            "현재 값 63.0%와 24시간 8.0%포인트, 7일 11.0%포인트 변화가 저장되었습니다. "
            "이 수치는 공개 예측시장 참여자 데이터의 관찰값입니다."
        ),
        conditional_scenarios=[
            {
                "title": "조건 확인",
                "basis": "market_definition",
                "narrative": (
                    "만약 test issue 조건이 문서에서 확인된다면 판정 조건과 함께 읽습니다."
                ),
            },
            {
                "title": "부분 확인",
                "basis": "market_definition",
                "narrative": "만약 test issue 자료가 불완전한 경우 후속 문서를 추가로 확인합니다.",
            },
            {
                "title": "조건 미확인",
                "basis": "market_definition",
                "narrative": "만약 test issue 조건이 확인되지 않는다면 미확인 상태로 구분합니다.",
            },
        ],
        factors_to_check=[
            {
                "title": "판정 문서",
                "basis": "market_definition",
                "explanation": "test issue의 조건이 적힌 공식 문서를 확인합니다.",
            },
            {
                "title": "기준 시각",
                "basis": "market_definition",
                "explanation": "자료가 정해진 기준일 안에 공개됐는지 확인합니다.",
            },
        ],
        signals_to_watch=[
            {
                "title": "공식 자료",
                "basis": "market_definition",
                "explanation": "test issue 관련 공식 자료의 공개 여부를 관찰합니다.",
            },
            {
                "title": "데이터 갱신",
                "basis": "observed_data",
                "explanation": "공개 예측시장 데이터의 이후 갱신을 확인합니다.",
            },
        ],
        evidence_synthesis=(
            "검증된 공식 자료에는 test issue 관련 공지가 기록되어 있습니다. "
            "이 자료와 관찰된 움직임 사이의 관계는 확인되지 않았습니다."
            if with_candidate
            else None
        ),
    )
    content = assemble_v5_report_content(inputs, fields)
    assert content is not None
    report.content = build_v5_stored_payload(inputs, content).model_dump(mode="json")
    report.prompt_version = "v5"
    db_session.commit()
    return report, candidate


def seed_v6_report(
    db_session,
    *,
    report_id: uuid.UUID = REPORT_ID_LATEST,
    generated_at: datetime = NOW + timedelta(minutes=5),
    with_candidate: bool = True,
    change_24h: float = 0.08,
) -> tuple[AiReport, ContextCandidate | None]:
    """Seed one strict v6 envelope plus its exact stored rule evidence."""
    report, candidate = seed_v4_report(
        db_session,
        report_id=report_id,
        generated_at=generated_at,
        with_candidate=with_candidate,
    )
    metric = db_session.get(MarketMetric, 1)
    metric.change_24h = change_24h
    candidate_inputs = []
    if candidate is not None:
        candidate_inputs = [
            V4VerifiedCandidateInput(
                id=candidate.id,
                title=candidate.event_title,
                event_at=candidate.event_at,
                neutral_summary=candidate.neutral_summary,
                sources=[V4ContextSource.model_validate(source) for source in candidate.sources],
            )
        ]
    rules = ResolutionRulesInput(
        condition_text="The documented test condition is recorded by the deadline.",
        deadline=NOW + timedelta(days=30),
        exclusions=[],
        resolution_source=None,
        source_description_hash="test-description-hash",
        rules_hash="test-rules-hash",
        collected_at=NOW - timedelta(minutes=10),
    )
    if db_session.query(MarketResolutionRule).count() == 0:
        db_session.add(
            MarketResolutionRule(
                id=uuid.uuid4(),
                market_id=MARKET_ID,
                condition_text=rules.condition_text,
                deadline=rules.deadline,
                exclusions=rules.exclusions,
                resolution_source=rules.resolution_source,
                source_description_hash=rules.source_description_hash,
                rules_hash=rules.rules_hash,
                collected_at=rules.collected_at,
            )
        )
    inputs = V4ReportInputs(
        market_id=MARKET_ID,
        metric_id=1,
        episode_at=NOW,
        data_as_of=NOW,
        title="Will the test issue resolve Yes?",
        description="A seeded test issue.",
        category="technology",
        outcome_label="Yes",
        end_date=NOW + timedelta(days=30),
        current_value=0.63,
        change_24h=change_24h,
        change_7d=0.11,
        confidence_level="sufficient",
        volume_24h=1000,
        liquidity=2000,
        context_candidates=candidate_inputs,
        resolution_rules=rules,
    )
    mode = determine_v6_report_mode(inputs)
    scenario = {
        "title": "문서 범위가 달라지는 경우",
        "text": (
            "만약 Test 항목을 다루는 공개 문서의 범위가 달라지는 경우 일반적인 "
            "상황 구분에 따라 내용을 살펴볼 수 있습니다."
        ),
        "basis": "general_scenario",
    }
    verified = {
        "text": (
            "Official 자료는 Test 항목과 관련된 공개 배경을 담고 있으며, "
            "관찰된 흐름과의 관계를 입증하지 않습니다."
        ),
        "basis": "verified_context",
        "candidate_ids": [str(CONTEXT_CANDIDATE_ID)],
    }
    material = {
        "scenario_index": 1,
        "title": "공개 문서 범위",
        "text": "Test 항목을 다루는 공식 공개 문서의 범위를 확인할 자료입니다.",
        "basis": "general_scenario",
    }
    if mode == "change_with_evidence":
        raw = {
            "mode": mode,
            "verified_background": verified,
            "conditional_interpretations": [
                {
                    "title": "자료 범위가 이어지는 경우",
                    "text": (
                        "만약 Official 후속 자료가 같은 Test 항목을 다루는 "
                        "경우 공개 배경의 범위를 조건부로 비교할 수 있습니다."
                    ),
                    "basis": "verified_context",
                    "candidate_ids": [str(CONTEXT_CANDIDATE_ID)],
                }
            ],
        }
    elif mode == "change_without_evidence":
        raw = {
            "mode": mode,
            "conditional_scenarios": [scenario],
            "materials_to_check": [material],
        }
    elif mode == "stable_with_evidence":
        raw = {
            "mode": mode,
            "issue_explanation": {
                "text": "이 이슈는 Test 항목이 공적 기록에서 다뤄지는 범위를 살펴봅니다.",
                "basis": "market_definition",
            },
            "verified_background": verified,
            "conditional_scenarios": [scenario],
        }
    else:
        raw = {
            "mode": mode,
            "issue_explanation": {
                "text": "이 이슈는 Test 항목을 이해하기 위한 일반적인 상황 구분을 다룹니다.",
                "basis": "general_scenario",
            },
            "conditional_scenarios": [scenario],
            "materials_to_check": [material],
        }
    briefing = parse_v6_briefing(json.dumps(raw, ensure_ascii=False), mode)
    assert briefing is not None
    payload = build_v6_stored_payload(inputs, briefing)
    assert payload is not None
    report.content = payload.model_dump(mode="json")
    report.prompt_version = "v6"
    db_session.commit()
    return report, candidate
