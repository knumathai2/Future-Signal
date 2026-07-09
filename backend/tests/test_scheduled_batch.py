"""Scheduled batch orchestration tests.

Uses in-memory SQLite and a fake LLM client only. No shared/dev/prod database
and no OpenAI network call is touched by this suite.
"""

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

from app.core.scheduled_batch import run_scheduled_batch
from app.db.models import (
    AiReport,
    Base,
    DataCollectionLog,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketSnapshot,
    RelatedEvent,
)

NOW = datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)
VALID_CONTENT = {
    "issue_summary": "This market tracks a public issue.",
    "movement_explanation": "Expectation rose over the past week.",
    "key_change_context": "No related event candidate is available this period.",
    "uncertainty_summary": "Trading activity has been moderate.",
    "neutral_conclusion": "Public expectation has shifted upward.",
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
            MarketOutcome.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            IssueSignal.__table__,
            AiReport.__table__,
            RelatedEvent.__table__,
            DataCollectionLog.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _normalized(condition_id: str = "0xcond-1", current_value: float = 0.6) -> dict:
    return {
        "polymarket_condition_id": condition_id,
        "title": "Will the test issue resolve Yes?",
        "description": "Tracks reflected expectation in public prediction-market data.",
        "category": "politics",
        "status": "active",
        "outcome_type": "binary",
        "outcome_label": "Yes",
        "current_value": current_value,
        "volume_24h": 1000.0,
        "volume_total": 10000.0,
        "liquidity": 2000.0,
        "market_created_at": "2026-01-01T00:00:00Z",
        "end_date": "2026-12-31T00:00:00Z",
        "price_history_token": "token-1",
    }


class FakeLLMClient:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls = 0

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return self._responses.pop(0)


def test_full_batch_writes_metrics_signals_logs_and_ai_report(db):
    client = FakeLLMClient([json.dumps(VALID_CONTENT)])

    result = run_scheduled_batch(
        db,
        normalized_markets=[_normalized()],
        llm_client=client,
        model_name="gpt-4o-mini",
    )

    assert result.error is None
    assert result.markets_processed == 1
    assert result.markets_failed == 0
    assert result.signals_inserted == 0  # first run has insufficient history
    assert result.reports_success == 1
    assert client.calls == 1
    assert db.query(MarketSnapshot).count() == 1
    assert db.query(MarketMetric).count() == 1
    assert db.query(AiReport).count() == 1
    assert db.query(AiReport).one().status == "success"
    log = db.query(DataCollectionLog).one()
    assert log.status == "scheduled_batch_success"
    assert log.markets_processed == 1


def test_full_batch_marks_empty_normalized_input_as_failed(db):
    client = FakeLLMClient([json.dumps(VALID_CONTENT)])

    result = run_scheduled_batch(
        db,
        normalized_markets=[],
        llm_client=client,
        model_name="gpt-4o-mini",
    )

    assert result.error == "RuntimeError: No normalized markets available for this batch run."
    assert result.normalized_count == 0
    assert result.markets_processed == 0
    assert result.reports_success == 0
    assert client.calls == 0
    assert db.query(MarketSnapshot).count() == 0
    assert db.query(MarketMetric).count() == 0
    assert db.query(AiReport).count() == 0
    log = db.query(DataCollectionLog).one()
    assert log.status == "scheduled_batch_failed"
    assert log.error_detail["error"] == result.error


def test_full_batch_detects_signal_before_ai_report_generation(db, monkeypatch):
    # Make the second collection run occur after 7d/24h baselines are usable.
    times = iter(
        [
            NOW,
            NOW + timedelta(seconds=1),
            NOW + timedelta(days=8),
            NOW + timedelta(days=8, seconds=1),
        ]
    )

    import app.core.snapshot_metrics as snapshot_metrics

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = next(times)
            return value if tz else value.replace(tzinfo=None)

    monkeypatch.setattr(snapshot_metrics, "datetime", FixedDateTime)
    first = run_scheduled_batch(
        db,
        normalized_markets=[_normalized(current_value=0.5)],
        llm_client=FakeLLMClient([json.dumps(VALID_CONTENT)]),
        model_name="gpt-4o-mini",
        record_log=False,
    )
    assert first.error is None

    second_client = FakeLLMClient([json.dumps(VALID_CONTENT)])
    second = run_scheduled_batch(
        db,
        normalized_markets=[_normalized(current_value=0.6)],
        llm_client=second_client,
        model_name="gpt-4o-mini",
        record_log=False,
    )

    assert second.error is None
    assert second.signals_inserted == 1
    assert second.reports_success == 1
    assert db.query(IssueSignal).count() == 1


def test_reports_only_uses_latest_existing_metric_run(db):
    market_id = uuid.uuid4()
    db.add(
        Market(
            id=market_id,
            polymarket_condition_id="0xcond-1",
            title="Will the test issue resolve Yes?",
            description="A seeded issue.",
            category="politics",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=30),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=30),
            last_seen_at=NOW,
        )
    )
    db.add(
        MarketSnapshot(
            market_id=market_id,
            captured_at=NOW,
            price=0.6,
            volume_24h=1000,
            volume_total=10000,
            liquidity=2000,
            best_bid=None,
            best_ask=None,
        )
    )
    db.add(
        MarketMetric(
            market_id=market_id,
            computed_at=NOW,
            change_24h=0.08,
            change_7d=0.1,
            volatility_score=None,
            attention_score=None,
            heat_score=90,
            confidence_level="sufficient",
        )
    )
    db.commit()

    client = FakeLLMClient([json.dumps(VALID_CONTENT)])
    result = run_scheduled_batch(
        db,
        llm_client=client,
        model_name="gpt-4o-mini",
        reports_only=True,
    )

    assert result.error is None
    assert result.reports_only is True
    assert result.markets_processed == 0
    assert result.reports_success == 1
    assert db.query(AiReport).count() == 1


def test_reports_only_uses_each_markets_latest_metric_not_only_global_max(db):
    for index, computed_at in enumerate([NOW, NOW + timedelta(seconds=1)], start=1):
        market_id = uuid.uuid4()
        db.add(
            Market(
                id=market_id,
                polymarket_condition_id=f"0xcond-{index}",
                title=f"Will test issue {index} resolve Yes?",
                description="A seeded issue.",
                category="politics",
                outcome_type="binary",
                status="active",
                market_created_at=NOW - timedelta(days=30),
                end_date=NOW + timedelta(days=30),
                first_seen_at=NOW - timedelta(days=30),
                last_seen_at=computed_at,
            )
        )
        db.add(
            MarketSnapshot(
                market_id=market_id,
                captured_at=computed_at,
                price=0.6,
                volume_24h=1000,
                volume_total=10000,
                liquidity=2000,
                best_bid=None,
                best_ask=None,
            )
        )
        db.add(
            MarketMetric(
                market_id=market_id,
                computed_at=computed_at,
                change_24h=0.08,
                change_7d=0.1,
                volatility_score=None,
                attention_score=None,
                heat_score=100 - index,
                confidence_level="sufficient",
            )
        )
    db.commit()

    client = FakeLLMClient([json.dumps(VALID_CONTENT), json.dumps(VALID_CONTENT)])
    result = run_scheduled_batch(
        db,
        llm_client=client,
        model_name="openai/gpt-4o-mini",
        reports_only=True,
    )

    assert result.error is None
    assert result.reports_only is True
    assert result.reports_success == 2
    assert client.calls == 2
    assert db.query(AiReport).count() == 2
