"""TASK-049: regeneration eligibility (new signal / no report / 24h stale),
the top-10-per-run cost-control cap, retry-once-then-fail handling, the
ADR-033 deterministic field assembly wired through the batch pipeline, and
the guarantee that a filtered/failed generation never disturbs the
previously stored successful report.

Uses an in-memory SQLite database (same pattern as
tests/test_signal_detection.py) - no shared/production database touched.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import BigInteger, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.ai_report import (
    CAUTION_NOTE_BY_LEVEL,
    POSSIBLE_DRIVERS_NO_CANDIDATE,
    POSSIBLE_DRIVERS_WITH_CANDIDATE,
    PROMPT_VERSION,
    V4_PROMPT_VERSION,
    V5_PROMPT_VERSION,
    V6_PROMPT_VERSION,
    LLMCallError,
    LLMReportFields,
    LLMUsage,
    assemble_report_content,
)
from app.core.ai_report_batch import (
    MAX_REPORTS_PER_BATCH_RUN,
    STALENESS_THRESHOLD,
    build_prompt_inputs_for_market,
    build_v4_inputs_for_market,
    generate_report_for_market,
    run_ai_report_batch,
    run_v4_ai_report_batch,
    run_v5_ai_report_batch,
    run_v6_ai_report_batch,
    select_markets_for_regeneration,
)
from app.core.historical_seed import metric_timestamp_for_seed
from app.db.models import (
    AiReport,
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

NOW = datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")

# The three LLM-authored fields only (ADR-033) - possible_drivers,
# external_context, what_to_check, data_limitations, and caution_note are
# assembled deterministically by app/core/ai_report.py, never LLM output.
VALID_LLM_RESPONSE = {
    "issue_overview": (
        "이 이슈는 정해진 기준일까지 특정 조건이 확인되는지를 공개 데이터 맥락에서 살펴봅니다."
    ),
    "current_data_reading": (
        "현재 공개 예측시장 참여자 데이터에서는 이 이슈가 일부 재평가되고 있으나, "
        "실제 결과를 뜻하지는 않습니다."
    ),
    "possible_outlook": (
        "이후 공개 데이터에서 관찰된 움직임의 지속 또는 완화가 확인되더라도, 이는 "
        "데이터의 흐름만 설명하며 현실의 결과를 입증하지 않습니다."
    ),
}

# A pre-existing/legacy stored report row's content - shape does not need to
# validate against the current schema since these rows only exercise
# regeneration-eligibility and storage-history assertions, never a live read.
LEGACY_CONTENT = {
    "issue_explainer": "이 이슈는 정해진 기준일까지 특정 조건이 확인되는지를 살펴봅니다.",
    "why_it_matters": "이 조건은 관련 정책 일정과 후속 절차를 이해하는 데 참고가 됩니다.",
    "current_reading": "현재 공개 데이터에서는 일부 재평가 흐름이 관측됩니다.",
    "scenario_major_change": "조건이 명확히 성립하면 관련 절차가 확인됩니다.",
    "scenario_limited_change": "논의는 이어지지만 실제 변화는 제한적일 수 있습니다.",
    "scenario_status_quo": "조건이 성립하지 않으면 기존 흐름이 대체로 유지될 수 있습니다.",
    "check_points": "확인할 지점은 공식 발표, 기준일, 후속 절차입니다.",
    "caution_note": "이 요약은 공개 데이터와 등록된 맥락을 정리한 것입니다.",
}

VALID_V6_CHANGE_WITHOUT_EVIDENCE = {
    "mode": "change_without_evidence",
    "conditional_scenarios": [
        {
            "title": "문서 범위가 달라지는 경우",
            "text": (
                "만약 Test 항목을 다루는 공개 문서의 범위가 달라지는 경우 일반적인 "
                "상황 구분에 따라 내용을 살펴볼 수 있습니다."
            ),
            "basis": "general_scenario",
        }
    ],
    "materials_to_check": [
        {
            "scenario_index": 1,
            "title": "공개 문서 범위",
            "text": "Test 항목을 다루는 공식 공개 문서의 범위를 확인할 자료입니다.",
            "basis": "general_scenario",
        }
    ],
}


def _expected_v3_content(db, market_id, computed_at) -> dict:
    """Builds the exact expected stored content for a market/metric pair by
    running the same deterministic assembly the production pipeline uses,
    so tests assert against the real contract rather than a hand-duplicated
    fixture that could silently drift from it."""
    market = db.get(Market, market_id)
    metric = db.execute(
        select(MarketMetric).where(
            MarketMetric.market_id == market_id, MarketMetric.computed_at == computed_at
        )
    ).scalar_one()
    inputs = build_prompt_inputs_for_market(db, market, metric, computed_at)
    content = assemble_report_content(inputs, LLMReportFields(**VALID_LLM_RESPONSE))
    return content.model_dump()


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
            MarketResolutionRule.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            IssueSignal.__table__,
            AiReport.__table__,
            RelatedEvent.__table__,
            ContextCandidate.__table__,
            ContextCollectionRun.__table__,
            DataCollectionLog.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_market(db, market_id: uuid.UUID = MARKET_ID, title: str = "Test issue") -> None:
    db.add(
        Market(
            id=market_id,
            polymarket_condition_id=f"cond-{market_id}",
            title=title,
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
    db.add(
        MarketResolutionRule(
            id=uuid.uuid4(),
            market_id=market_id,
            condition_text="The documented test condition is recorded by the deadline.",
            deadline=NOW + timedelta(days=30),
            exclusions=[],
            resolution_source=None,
            source_description_hash="test-description-hash",
            rules_hash=f"test-rules-hash-{market_id}",
            collected_at=NOW - timedelta(minutes=10),
        )
    )
    db.commit()


def _snapshot(market_id: uuid.UUID, captured_at: datetime, price: float = 0.6) -> MarketSnapshot:
    return MarketSnapshot(
        market_id=market_id,
        captured_at=captured_at,
        price=price,
        volume_24h=1000,
        volume_total=5000,
        liquidity=2000,
        best_bid=price - 0.01,
        best_ask=price + 0.01,
    )


def _metric(
    market_id: uuid.UUID,
    computed_at: datetime,
    heat_score: float = 40.0,
    change_24h: float | None = 0.08,
) -> MarketMetric:
    return MarketMetric(
        market_id=market_id,
        computed_at=computed_at,
        change_24h=change_24h,
        change_7d=0.1,
        volatility_score=None,
        attention_score=None,
        heat_score=heat_score,
        confidence_level="sufficient",
    )


class FakeLLMClient:
    """Scripted `LLMClient`: `responses` is consumed in order. A list entry
    that's an `Exception` instance is raised via `LLMCallError`; anything
    else is returned as the raw text."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.calls = 0

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


VALID_V4_RESPONSE = {
    "issue_overview": ("이 이슈는 문서에 적힌 조건이 정해진 기준 안에서 확인되는지를 살펴봅니다."),
    "what_to_check": (
        "게시된 조건 문구와 이후 공개되는 자료 및 데이터 갱신 내용을 추가로 확인해야 합니다."
    ),
}

VALID_V5_RESPONSE = {
    "executive_summary": (
        "Test issue의 문서 조건을 정해진 기준일까지 확인하는 이슈입니다. 저장된 현재 값과 "
        "최근 비교 구간의 움직임을 함께 정리하지만 현실의 결과나 배경을 뜻하지 않습니다."
    ),
    "current_data_interpretation": (
        "저장된 현재 값과 최근 비교값은 참여자 데이터의 관찰 흐름을 보여줍니다. "
        "이 움직임만으로 현실의 결과나 배경을 판단할 수 없습니다."
    ),
    "conditional_scenarios": [
        {
            "title": "조건 확인",
            "basis": "market_definition",
            "narrative": (
                "만약 test issue 조건이 공식 문서에서 확인된다면 해당 판정 조건과 함께 읽습니다."
            ),
        },
        {
            "title": "부분 확인",
            "basis": "market_definition",
            "narrative": (
                "만약 test issue 관련 자료가 공개되지만 조건 충족이 "
                "불분명한 경우 후속 문서를 확인합니다."
            ),
        },
        {
            "title": "조건 미확인",
            "basis": "market_definition",
            "narrative": (
                "만약 기준일까지 test issue 조건이 공식 문서에서 확인되지 않는다면 "
                "미확인 상태로 구분합니다."
            ),
        },
    ],
    "factors_to_check": [
        {
            "title": "판정 문서",
            "explanation": "test issue의 조건을 명시한 공식 문서를 확인합니다.",
            "basis": "market_definition",
        },
        {
            "title": "기준 시각",
            "explanation": "자료가 정해진 기준일 안에 공개됐는지 확인합니다.",
            "basis": "market_definition",
        },
    ],
    "signals_to_watch": [
        {
            "title": "공식 자료",
            "explanation": "test issue 관련 공식 문서의 공개 여부를 관찰합니다.",
            "basis": "market_definition",
        },
        {
            "title": "데이터 갱신",
            "explanation": "공개 예측시장 데이터의 이후 갱신을 별도로 확인합니다.",
            "basis": "observed_data",
        },
    ],
    "evidence_synthesis": None,
}


class FakeV4LLMClient(FakeLLMClient):
    def __init__(self, responses: list, *, cost_usd=0.03):
        super().__init__(responses)
        self.cost_usd = cost_usd
        self.usage_records = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = super().complete(system_prompt, user_prompt)
        self.usage_records.append(
            LLMUsage(input_tokens=40, output_tokens=10, cost_usd=self.cost_usd)
        )
        return response


def _seed_v4_context(
    db,
    *,
    market_id=MARKET_ID,
    episode_at=NOW,
    state="verified",
    with_sources=True,
):
    candidate_id = uuid.uuid4()
    sources = (
        [
            {
                "citation_id": "citation:a",
                "title": "Official source",
                "url": "https://example.gov/update",
                "canonical_url": "https://example.gov/update",
                "domain": "example.gov",
                "source_type": "official",
                "content_hash": "sha256:source",
            }
        ]
        if with_sources
        else []
    )
    db.add(
        ContextCandidate(
            id=candidate_id,
            market_id=market_id,
            episode_at=episode_at,
            event_title="공개 정보 업데이트",
            event_at=episode_at,
            neutral_summary="공식 출처는 같은 검토 구간에 관련 정보를 기록했습니다.",
            sources=sources,
            verification_state=state,
            verification_score_internal=1,
            research_model="openai/research",
            verifier_model="anthropic/verifier",
            policy_version="v4",
            evidence_hash=f"sha256:{candidate_id}",
            collected_at=episode_at,
            expires_at=episode_at + timedelta(hours=24),
        )
    )
    db.add(
        ContextCollectionRun(
            id=uuid.uuid4(),
            market_id=market_id,
            episode_at=episode_at,
            started_at=episode_at,
            finished_at=episode_at,
            status="success" if state == "verified" else "no_candidate",
            query_count=1,
            result_count=1,
            accepted_count=1 if state == "verified" else 0,
            model_usage={"research_cost_usd": 0.01, "verifier_cost_usd": 0.01},
            error_detail=None,
        )
    )
    db.commit()
    return candidate_id


# --- select_markets_for_regeneration --------------------------------------


def test_market_with_new_signal_this_run_qualifies(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        IssueSignal(
            market_id=MARKET_ID,
            signal_type="expectation_shift",
            severity="medium",
            window="24h",
            magnitude=0.08,
            triggered_at=NOW,
            detail=None,
        )
    )
    db.commit()

    qualifying = select_markets_for_regeneration(db, NOW)
    assert [m.market_id for m in qualifying] == [MARKET_ID]


def test_market_with_no_ai_reports_row_qualifies(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()

    qualifying = select_markets_for_regeneration(db, NOW)
    assert [m.market_id for m in qualifying] == [MARKET_ID]


def test_market_with_stale_report_qualifies(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            generated_at=NOW - STALENESS_THRESHOLD - timedelta(minutes=1),
            input_metrics_id=None,
            content=LEGACY_CONTENT,
            model_used="gpt-4o-mini",
            prompt_version="v1",
            status="success",
        )
    )
    db.commit()

    qualifying = select_markets_for_regeneration(db, NOW)
    assert [m.market_id for m in qualifying] == [MARKET_ID]


def test_market_with_fresh_report_and_no_new_signal_does_not_qualify(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            generated_at=NOW - timedelta(hours=1),
            input_metrics_id=None,
            content=LEGACY_CONTENT,
            model_used="gpt-4o-mini",
            prompt_version=PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()

    assert select_markets_for_regeneration(db, NOW) == []


def test_current_prompt_version_prevents_regeneration_when_timestamp_ties(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    for prompt_version in ["v1", PROMPT_VERSION]:
        db.add(
            AiReport(
                id=uuid.uuid4(),
                market_id=MARKET_ID,
                generated_at=NOW - timedelta(hours=1),
                input_metrics_id=None,
                content=LEGACY_CONTENT,
                model_used="gpt-4o-mini",
                prompt_version=prompt_version,
                status="success",
            )
        )
    db.commit()

    assert select_markets_for_regeneration(db, NOW) == []


def test_market_with_fresh_legacy_prompt_version_qualifies_for_regeneration(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            generated_at=NOW - timedelta(hours=1),
            input_metrics_id=None,
            content=LEGACY_CONTENT,
            model_used="gpt-4o-mini",
            prompt_version="v1",
            status="success",
        )
    )
    db.commit()

    qualifying = select_markets_for_regeneration(db, NOW)
    assert [m.market_id for m in qualifying] == [MARKET_ID]


def test_only_failed_report_still_counts_as_no_successful_report(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            generated_at=NOW - timedelta(minutes=5),
            input_metrics_id=None,
            content={},
            model_used="gpt-4o-mini",
            prompt_version="v1",
            status="failed",
        )
    )
    db.commit()

    qualifying = select_markets_for_regeneration(db, NOW)
    assert [m.market_id for m in qualifying] == [MARKET_ID]


def test_cap_is_top_10_by_heat_score(db):
    market_ids = [uuid.uuid4() for _ in range(15)]
    for i, market_id in enumerate(market_ids):
        _seed_market(db, market_id=market_id, title=f"Issue {i}")
        db.add(_snapshot(market_id, NOW))
        db.add(_metric(market_id, NOW, heat_score=float(i)))  # 0..14
    db.commit()

    qualifying = select_markets_for_regeneration(db, NOW)

    assert len(qualifying) == MAX_REPORTS_PER_BATCH_RUN
    scores = [float(m.heat_score) for m in qualifying]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 14.0  # highest heat_score wins a slot


def test_only_evaluates_metrics_computed_in_this_run(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW - timedelta(hours=6)))
    db.add(_metric(MARKET_ID, NOW - timedelta(hours=6)))
    db.commit()

    assert select_markets_for_regeneration(db, NOW) == []


# --- build_prompt_inputs_for_market ----------------------------------------


def _inputs_for(db, market_id=MARKET_ID, computed_at=NOW):
    market = db.get(Market, market_id)
    metric = db.execute(
        select(MarketMetric).where(
            MarketMetric.market_id == market_id, MarketMetric.computed_at == computed_at
        )
    ).scalar_one()
    inputs = build_prompt_inputs_for_market(db, market, metric, computed_at)
    return market, metric, inputs


def test_prompt_inputs_use_latest_snapshot_at_or_before_metric_timestamp(db):
    _seed_market(db)
    latest_snapshot_at = NOW
    metric_at = metric_timestamp_for_seed(latest_snapshot_at)
    db.add(_snapshot(MARKET_ID, NOW - timedelta(hours=1), price=0.42))
    db.add(_snapshot(MARKET_ID, latest_snapshot_at, price=0.67))
    db.add(_metric(MARKET_ID, metric_at))
    db.commit()
    market = db.get(Market, MARKET_ID)
    metric = db.execute(select(MarketMetric)).scalar_one()

    inputs = build_prompt_inputs_for_market(db, market, metric, metric_at)

    assert inputs is not None
    assert inputs.current_value == pytest.approx(0.67)


def test_no_snapshot_at_or_before_metric_timestamp_is_skipped_without_fabricating(db):
    _seed_market(db)
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market = db.get(Market, MARKET_ID)
    metric = db.execute(select(MarketMetric)).scalar_one()

    assert build_prompt_inputs_for_market(db, market, metric, NOW) is None


def test_future_only_snapshot_is_not_used_for_prompt_inputs(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW + timedelta(microseconds=1), price=0.91))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market = db.get(Market, MARKET_ID)
    metric = db.execute(select(MarketMetric)).scalar_one()

    assert build_prompt_inputs_for_market(db, market, metric, NOW) is None


def test_prompt_inputs_include_tracked_outcome_label_and_end_date(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        MarketOutcome(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            outcome_label="Yes",
            token_id="token-1",
            is_tracked=True,
        )
    )
    db.commit()

    _, _, inputs = _inputs_for(db)
    assert inputs.outcome_label == "Yes"
    assert inputs.end_date.replace(tzinfo=UTC) == NOW + timedelta(days=30)


def test_prompt_inputs_have_no_related_event_fields_when_none_curated(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()

    _, _, inputs = _inputs_for(db)
    assert inputs.related_event_title is None
    assert inputs.related_event_date is None
    assert inputs.related_event_note is None


def test_prompt_inputs_include_curated_related_event_title_date_and_note_separately(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    event_date = datetime(2026, 2, 18, tzinfo=UTC)
    db.add(
        RelatedEvent(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            event_title="Curated Context Event",
            event_date=event_date,
            note="Candidate context for review; not presented as a cause.",
        )
    )
    db.commit()

    _, _, inputs = _inputs_for(db)
    assert inputs.related_event_title == "Curated Context Event"
    assert inputs.related_event_date.replace(tzinfo=UTC) == event_date
    assert inputs.related_event_note == "Candidate context for review; not presented as a cause."


# --- generate_report_for_market -------------------------------------------


def test_successful_generation_stores_success_row(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "success"
    stored = db.execute(select(AiReport)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "success"
    assert stored[0].content == _expected_v3_content(db, MARKET_ID, NOW)
    assert client.calls == 1


def test_successful_generation_uses_no_candidate_possible_drivers_when_none_curated(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    stored = db.execute(select(AiReport)).scalars().all()
    assert stored[0].content["possible_drivers"] == POSSIBLE_DRIVERS_NO_CANDIDATE
    assert stored[0].content["external_context"] is None


def test_successful_generation_uses_with_candidate_possible_drivers_when_curated(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        RelatedEvent(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            event_title="Curated Context Event",
            event_date=datetime(2026, 2, 18, tzinfo=UTC),
            note="Candidate context for review; not presented as a cause.",
        )
    )
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    stored = db.execute(select(AiReport)).scalars().all()
    assert stored[0].content["possible_drivers"] == POSSIBLE_DRIVERS_WITH_CANDIDATE.format(
        title="Curated Context Event", date="2026-02-18"
    )
    assert "Curated Context Event" in stored[0].content["possible_drivers"]
    assert "2026-02-18" in stored[0].content["possible_drivers"]
    assert (
        stored[0].content["external_context"]
        == "Candidate context for review; not presented as a cause."
    )


def test_successful_generation_uses_deterministic_caution_note_for_confidence_level(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    stored = db.execute(select(AiReport)).scalars().all()
    assert stored[0].content["caution_note"] == CAUTION_NOTE_BY_LEVEL["sufficient"]


def test_one_transient_error_then_success_is_retried_and_stored(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([LLMCallError("timeout"), json.dumps(VALID_LLM_RESPONSE)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "success"
    assert client.calls == 2
    stored = db.execute(select(AiReport)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "success"


def test_two_consecutive_errors_records_failed_and_keeps_previous_report(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    previous = AiReport(
        id=uuid.uuid4(),
        market_id=MARKET_ID,
        generated_at=NOW - timedelta(hours=1),
        input_metrics_id=None,
        content=LEGACY_CONTENT,
        model_used="gpt-4o-mini",
        prompt_version="v1",
        status="success",
    )
    db.add(previous)
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([LLMCallError("timeout"), LLMCallError("timeout again")])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "failed"
    assert client.calls == 2  # exactly one retry, never more

    rows = db.execute(select(AiReport).order_by(AiReport.generated_at)).scalars().all()
    assert len(rows) == 2
    assert rows[-1].status == "failed"

    # the service-facing "previous report" is still the latest *successful* row
    latest_success = db.execute(
        select(AiReport)
        .where(AiReport.market_id == MARKET_ID, AiReport.status == "success")
        .order_by(AiReport.generated_at.desc())
        .limit(1)
    ).scalar_one()
    assert latest_success.id == previous.id
    assert latest_success.content == LEGACY_CONTENT


def test_malformed_json_is_treated_as_failure_not_partially_parsed(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient(["{not valid json", "{not valid json either"])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "failed"
    stored = db.execute(select(AiReport)).scalars().all()
    assert stored[0].status == "failed"
    assert stored[0].content == {}


def test_llm_field_below_minimum_length_is_treated_as_failure(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    too_short = dict(VALID_LLM_RESPONSE, issue_overview="Too short.")
    client = FakeLLMClient([json.dumps(too_short), json.dumps(too_short)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "failed"
    assert outcome.reason == "assembled_content_failed_v3_bounds"
    assert client.calls == 2


def test_filter_failure_discards_output_and_does_not_touch_ai_reports(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    previous = AiReport(
        id=uuid.uuid4(),
        market_id=MARKET_ID,
        generated_at=NOW - timedelta(hours=1),
        input_metrics_id=None,
        content=LEGACY_CONTENT,
        model_used="gpt-4o-mini",
        prompt_version="v1",
        status="success",
    )
    db.add(previous)
    db.commit()
    market, metric, inputs = _inputs_for(db)

    unsafe_response = dict(
        VALID_LLM_RESPONSE,
        possible_outlook=(
            "이 이슈에 대해 우리는 매수를 추천합니다. 이는 확실한 수익 기회입니다. "
            "충분히 긴 문장을 위해 추가 설명을 덧붙입니다."
        ),
    )
    client = FakeLLMClient([json.dumps(unsafe_response)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "filtered"
    assert client.calls == 1  # filter failures are never retried

    rows = db.execute(select(AiReport)).scalars().all()
    assert len(rows) == 1  # only the pre-seeded previous row - nothing new stored
    assert rows[0].id == previous.id


def test_external_context_missing_qualifier_is_filtered_before_storage(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.add(
        RelatedEvent(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            event_title="Curated Context Event",
            event_date=datetime(2026, 2, 18, tzinfo=UTC),
            note=(
                "This narrative note has no qualifier at all, just filler "
                "text to satisfy the minimum length requirement here."
            ),
        )
    )
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "filtered"
    assert outcome.reason == (
        "external_context:external_context_missing_candidate_not_cause_qualifier"
    )
    stored = db.execute(select(AiReport)).scalars().all()
    assert stored == []


# --- run_ai_report_batch (end to end) -------------------------------------


def test_batch_run_generates_for_qualifying_markets_only(db):
    _seed_market(db, market_id=MARKET_ID, title="Qualifies (no report yet)")
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW, heat_score=90.0))

    other_id = uuid.uuid4()
    _seed_market(db, market_id=other_id, title="Does not qualify (fresh report)")
    db.add(_snapshot(other_id, NOW))
    db.add(_metric(other_id, NOW, heat_score=50.0))
    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=other_id,
            generated_at=NOW - timedelta(hours=1),
            input_metrics_id=None,
            content=LEGACY_CONTENT,
            model_used="gpt-4o-mini",
            prompt_version=PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    outcomes = run_ai_report_batch(db, NOW, client, "gpt-4o-mini")

    assert len(outcomes) == 1
    assert outcomes[0].market_id == MARKET_ID
    assert outcomes[0].status == "success"


def test_batch_run_stores_success_when_metric_is_after_latest_snapshot(db):
    _seed_market(db)
    latest_snapshot_at = NOW
    metric_at = metric_timestamp_for_seed(latest_snapshot_at)
    db.add(_snapshot(MARKET_ID, latest_snapshot_at, price=0.64))
    db.add(_metric(MARKET_ID, metric_at, heat_score=90.0))
    db.commit()
    metric = db.execute(select(MarketMetric)).scalar_one()

    client = FakeLLMClient([json.dumps(VALID_LLM_RESPONSE)])
    outcomes = run_ai_report_batch(db, metric_at, client, "gpt-4o-mini")

    assert len(outcomes) == 1
    assert outcomes[0].market_id == MARKET_ID
    assert outcomes[0].status == "success"
    assert client.calls == 1
    stored = db.execute(select(AiReport)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "success"
    assert stored[0].input_metrics_id == metric.id


# --- ADR-038 v4 evidence report batch ------------------------------------


def _seed_v4_metric_state(db, *, with_context=True, with_sources=True):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW, price=0.63))
    db.add(_metric(MARKET_ID, NOW, heat_score=90.0, change_24h=0.08))
    db.commit()
    candidate_id = None
    if with_context:
        candidate_id = _seed_v4_context(db, with_sources=with_sources)
    else:
        db.add(
            ContextCollectionRun(
                id=uuid.uuid4(),
                market_id=MARKET_ID,
                episode_at=NOW,
                started_at=NOW,
                finished_at=NOW,
                status="no_candidate",
                query_count=1,
                result_count=0,
                accepted_count=0,
                model_usage={"research_cost_usd": 0.01, "verifier_cost_usd": 0.01},
                error_detail=None,
            )
        )
        db.commit()
    metric = db.execute(select(MarketMetric)).scalar_one()
    market = db.get(Market, MARKET_ID)
    return market, metric, candidate_id


def test_v4_inputs_load_only_verified_same_episode_candidates_with_sources(db):
    market, metric, candidate_id = _seed_v4_metric_state(db)
    _seed_v4_context(db, episode_at=NOW - timedelta(hours=2), state="verified")
    _seed_v4_context(db, episode_at=NOW, state="withheld")

    inputs = build_v4_inputs_for_market(db, market, metric, NOW)

    assert inputs is not None
    assert inputs.metric_id == metric.id
    assert [candidate.id for candidate in inputs.context_candidates] == [candidate_id]
    assert inputs.data_as_of == NOW


def test_v4_inputs_load_reference_values_at_or_before_window_boundaries(db):
    market, metric, _ = _seed_v4_metric_state(db, with_context=False)
    db.add(_snapshot(MARKET_ID, NOW - timedelta(hours=25), price=0.55))
    db.add(_snapshot(MARKET_ID, NOW - timedelta(days=8), price=0.53))
    db.commit()

    inputs = build_v4_inputs_for_market(db, market, metric, NOW)

    assert inputs is not None
    assert inputs.value_24h_ago == pytest.approx(0.55)
    assert inputs.value_24h_ago_at == NOW - timedelta(hours=25)
    assert inputs.value_7d_ago == pytest.approx(0.53)
    assert inputs.value_7d_ago_at == NOW - timedelta(days=8)
    assert inputs.recent_history_summary is not None
    assert inputs.recent_history_summary.start_value == pytest.approx(0.55)
    assert inputs.recent_history_summary.end_value == pytest.approx(0.63)
    assert inputs.recent_history_summary.sample_count == 2


def test_v4_success_stores_payload_with_metric_and_candidate_evidence(db):
    _, metric, candidate_id = _seed_v4_metric_state(db)
    client = FakeV4LLMClient([json.dumps(VALID_V4_RESPONSE, ensure_ascii=False)])

    outcomes = run_v4_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "success"
    assert outcomes[0].model_usage["writer_cost_usd"] == 0.03
    row = db.query(AiReport).one()
    assert row.prompt_version == V4_PROMPT_VERSION
    assert row.status == "success"
    assert row.input_metrics_id == metric.id
    assert row.content["evidence_refs"] == [
        f"metric:{metric.id}",
        f"candidate:{candidate_id}",
    ]
    assert row.content["context_candidate_ids"] == [str(candidate_id)]
    assert row.content["content"]["context_summary"] is not None


def test_v4_no_candidate_stores_null_context_without_absence_narrative(db):
    _, metric, _ = _seed_v4_metric_state(db, with_context=False)
    client = FakeV4LLMClient([json.dumps(VALID_V4_RESPONSE, ensure_ascii=False)])

    outcomes = run_v4_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "success"
    row = db.query(AiReport).one()
    assert row.content["content"]["context_summary"] is None
    assert row.content["context_candidate_ids"] == []
    assert row.content["evidence_refs"] == [f"metric:{metric.id}"]


def test_v5_no_candidate_stores_narrative_and_metric_evidence(db):
    _, metric, _ = _seed_v4_metric_state(db, with_context=False)
    client = FakeV4LLMClient([json.dumps(VALID_V5_RESPONSE, ensure_ascii=False)])

    outcomes = run_v5_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "success"
    row = db.query(AiReport).one()
    assert row.prompt_version == V5_PROMPT_VERSION
    assert row.content["evidence_refs"] == [f"metric:{metric.id}"]
    assert row.content["content"]["evidence_synthesis"] is None
    assert "Test issue" in row.content["content"]["executive_summary"]


def test_v6_batch_stores_only_mode_constrained_payload(db):
    _, metric, _ = _seed_v4_metric_state(db, with_context=False)
    client = FakeV4LLMClient([json.dumps(VALID_V6_CHANGE_WITHOUT_EVIDENCE, ensure_ascii=False)])

    outcomes = run_v6_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "success"
    row = db.query(AiReport).one()
    assert row.prompt_version == V6_PROMPT_VERSION
    assert row.input_metrics_id == metric.id
    assert row.content["report_mode"] == "change_without_evidence"
    assert row.content["briefing"]["mode"] == "change_without_evidence"
    assert row.content["observed_change"] == {
        "metric_id": metric.id,
        "window": "24h",
        "current_value": 0.63,
        "change_value": 0.08,
        "significant": True,
        "threshold": 0.05,
    }
    assert row.content["evidence_refs"] == [f"metric:{metric.id}"]
    assert "current_value" not in row.content["briefing"]


def test_v5_generic_summary_is_filtered_and_not_stored(db):
    _seed_v4_metric_state(db, with_context=False)
    generic = dict(VALID_V5_RESPONSE)
    generic["executive_summary"] = (
        "이 항목은 문서 조건을 기준일까지 확인하는 일반적인 이슈입니다. 저장된 현재 값과 "
        "최근 비교 구간을 함께 정리하지만 현실의 결과나 배경을 뜻하지 않습니다."
    )
    generic["factors_to_check"] = [
        {
            "title": "문서 확인",
            "explanation": "정해진 문서 조건을 이후 공개 자료에서 확인합니다.",
            "basis": "market_definition",
        },
        {
            "title": "시각 확인",
            "explanation": "정해진 기준일 안의 공개 여부를 확인합니다.",
            "basis": "market_definition",
        },
    ]
    client = FakeV4LLMClient([json.dumps(generic, ensure_ascii=False)])

    outcomes = run_v5_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "filtered"
    assert outcomes[0].reason == "executive_summary:generic_summary"
    assert db.query(AiReport).count() == 0


def test_v4_malformed_fields_retry_once_then_store_failed_audit_row(db):
    _seed_v4_metric_state(db)
    client = FakeV4LLMClient(["not-json", json.dumps({"wrong": "shape"})])

    outcomes = run_v4_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "failed"
    assert client.calls == 2
    row = db.query(AiReport).one()
    assert row.status == "failed"
    assert row.prompt_version == V4_PROMPT_VERSION
    assert row.content == {}


def test_v4_verified_candidate_without_sources_fails_closed_before_writer(db):
    _seed_v4_metric_state(db, with_sources=False)
    client = FakeV4LLMClient([json.dumps(VALID_V4_RESPONSE, ensure_ascii=False)])

    outcomes = run_v4_ai_report_batch(db, NOW, client, "openai/writer")

    assert outcomes[0].status == "skipped"
    assert outcomes[0].reason == "invalid_or_missing_v4_evidence"
    assert client.calls == 0
    assert db.query(AiReport).count() == 0


def test_v4_failed_context_preserves_previous_successful_report(db):
    _seed_v4_metric_state(db)
    previous = AiReport(
        id=uuid.uuid4(),
        market_id=MARKET_ID,
        generated_at=NOW - timedelta(hours=25),
        input_metrics_id=None,
        content={"historical": True},
        model_used="openai/writer",
        prompt_version=V4_PROMPT_VERSION,
        status="success",
    )
    db.add(previous)
    db.commit()
    client = FakeV4LLMClient([json.dumps(VALID_V4_RESPONSE, ensure_ascii=False)])

    outcomes = run_v4_ai_report_batch(
        db,
        NOW,
        client,
        "openai/writer",
        failed_context_market_ids={MARKET_ID},
    )

    assert outcomes[0].status == "skipped"
    assert outcomes[0].reason == "context_research_failed"
    assert client.calls == 0
    assert db.query(AiReport).count() == 1
    assert db.get(AiReport, previous.id).content == {"historical": True}


def test_v4_legacy_v3_success_does_not_block_regeneration(db):
    _seed_v4_metric_state(db)
    db.add(
        AiReport(
            id=uuid.uuid4(),
            market_id=MARKET_ID,
            generated_at=NOW,
            input_metrics_id=None,
            content=LEGACY_CONTENT,
            model_used="legacy",
            prompt_version=PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()

    metrics = select_markets_for_regeneration(db, NOW, V4_PROMPT_VERSION)

    assert [metric.market_id for metric in metrics] == [MARKET_ID]


def test_v4_writer_budget_reservation_stops_before_call(db):
    _seed_v4_metric_state(db)
    db.add(
        DataCollectionLog(
            run_started_at=NOW - timedelta(hours=1),
            run_finished_at=NOW - timedelta(hours=1),
            status="scheduled_batch_success",
            markets_processed=1,
            markets_failed=0,
            error_detail={"v4_writer_cost_usd": 99.0},
        )
    )
    db.commit()
    client = FakeV4LLMClient([json.dumps(VALID_V4_RESPONSE, ensure_ascii=False)])

    outcomes = run_v4_ai_report_batch(
        db,
        NOW,
        client,
        "openai/writer",
        budget_usd=100,
        writer_cost_reservation_usd=1,
    )

    # The context seed already recorded USD 0.02, so 99.02 + 1 exceeds the cap.
    assert outcomes[0].status == "skipped"
    assert outcomes[0].reason == "budget_limit"
    assert client.calls == 0
