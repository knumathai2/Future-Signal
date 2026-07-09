"""TASK-015: regeneration eligibility (new signal / no report / 24h stale),
the top-10-per-run cost-control cap, retry-once-then-fail handling, and the
guarantee that a filtered/failed generation never disturbs the previously
stored successful report.

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

from app.core.ai_report import PROMPT_VERSION, LLMCallError
from app.core.ai_report_batch import (
    MAX_REPORTS_PER_BATCH_RUN,
    STALENESS_THRESHOLD,
    build_prompt_inputs_for_market,
    generate_report_for_market,
    run_ai_report_batch,
    select_markets_for_regeneration,
)
from app.core.historical_seed import metric_timestamp_for_seed
from app.db.models import (
    AiReport,
    Base,
    IssueSignal,
    Market,
    MarketMetric,
    MarketSnapshot,
    RelatedEvent,
)

NOW = datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")

VALID_CONTENT = {
    "issue_explainer": "이 이슈는 정해진 기준일까지 특정 조건이 확인되는지를 살펴봅니다.",
    "why_it_matters": "이 조건은 관련 정책 일정과 후속 절차를 이해하는 데 참고가 됩니다.",
    "current_reading": "현재 공개 데이터에서는 일부 재평가 흐름이 관측됩니다.",
    "scenario_major_change": "조건이 명확히 성립하면 관련 절차가 확인됩니다.",
    "scenario_limited_change": "논의는 이어지지만 실제 변화는 제한적일 수 있습니다.",
    "scenario_status_quo": "조건이 성립하지 않으면 기존 흐름이 대체로 유지될 수 있습니다.",
    "check_points": "확인할 지점은 공식 발표, 기준일, 후속 절차입니다.",
    "caution_note": "이 요약은 공개 데이터와 등록된 맥락을 정리한 것입니다.",
}


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
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            IssueSignal.__table__,
            AiReport.__table__,
            RelatedEvent.__table__,
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
            content=VALID_CONTENT,
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
            content=VALID_CONTENT,
            model_used="gpt-4o-mini",
            prompt_version=PROMPT_VERSION,
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
            content=VALID_CONTENT,
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


# --- generate_report_for_market -------------------------------------------


def _inputs_for(db, market_id=MARKET_ID, computed_at=NOW):
    market = db.get(Market, market_id)
    metric = db.execute(
        select(MarketMetric).where(
            MarketMetric.market_id == market_id, MarketMetric.computed_at == computed_at
        )
    ).scalar_one()
    inputs = build_prompt_inputs_for_market(db, market, metric, computed_at)
    return market, metric, inputs


def test_successful_generation_stores_success_row(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([json.dumps(VALID_CONTENT)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "success"
    stored = db.execute(select(AiReport)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "success"
    assert stored[0].content == VALID_CONTENT
    assert client.calls == 1


def test_one_transient_error_then_success_is_retried_and_stored(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    db.commit()
    market, metric, inputs = _inputs_for(db)

    client = FakeLLMClient([LLMCallError("timeout"), json.dumps(VALID_CONTENT)])
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
        content=VALID_CONTENT,
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
    assert latest_success.content == VALID_CONTENT


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


def test_filter_failure_discards_output_and_does_not_touch_ai_reports(db):
    _seed_market(db)
    db.add(_snapshot(MARKET_ID, NOW))
    db.add(_metric(MARKET_ID, NOW))
    previous = AiReport(
        id=uuid.uuid4(),
        market_id=MARKET_ID,
        generated_at=NOW - timedelta(hours=1),
        input_metrics_id=None,
        content=VALID_CONTENT,
        model_used="gpt-4o-mini",
        prompt_version="v1",
        status="success",
    )
    db.add(previous)
    db.commit()
    market, metric, inputs = _inputs_for(db)

    unsafe_content = dict(VALID_CONTENT, caution_note="We recommend you buy into this now.")
    client = FakeLLMClient([json.dumps(unsafe_content)])
    outcome = generate_report_for_market(db, market, metric, inputs, client, NOW, "gpt-4o-mini")

    assert outcome.status == "filtered"
    assert client.calls == 1  # filter failures are never retried

    rows = db.execute(select(AiReport)).scalars().all()
    assert len(rows) == 1  # only the pre-seeded previous row - nothing new stored
    assert rows[0].id == previous.id


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
            content=VALID_CONTENT,
            model_used="gpt-4o-mini",
            prompt_version=PROMPT_VERSION,
            status="success",
        )
    )
    db.commit()

    client = FakeLLMClient([json.dumps(VALID_CONTENT)])
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

    client = FakeLLMClient([json.dumps(VALID_CONTENT)])
    outcomes = run_ai_report_batch(db, metric_at, client, "gpt-4o-mini")

    assert len(outcomes) == 1
    assert outcomes[0].market_id == MARKET_ID
    assert outcomes[0].status == "success"
    assert client.calls == 1
    stored = db.execute(select(AiReport)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "success"
    assert stored[0].input_metrics_id == metric.id
