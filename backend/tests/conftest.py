"""Shared test fixtures.

Registers a SQLite-compatible compile rule for the Postgres-only JSONB
column type so backend/app/db/models.py's DDL can be created against an
in-memory SQLite DB for tests. This is a local/dev-only test fixture per
TASK-010's constraint against applying migrations.py/001_initial_schema.sql
to any shared or production database - the override only affects the
"sqlite" dialect used here and never touches the real Postgres path.
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import categories as categories_routes
from app.api.routes import issues as issues_routes
from app.db.models import (
    AiReport,
    Base,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
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


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


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
            title="Will the test issue resolve Yes?",
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


def report_content(label: str) -> dict[str, str]:
    return {
        "issue_explainer": f"{label} issue explainer from stored data.",
        "why_it_matters": f"{label} issue context is described in plain language.",
        "current_reading": f"{label} current reading is based on stored metrics.",
        "scenario_major_change": f"{label} major-change scenario is conditional context.",
        "scenario_limited_change": f"{label} limited-change scenario is conditional context.",
        "scenario_status_quo": f"{label} status-quo scenario is conditional context.",
        "check_points": f"{label} checkpoints summarize dates and formal updates.",
        "caution_note": f"{label} caution note avoids any outcome claim.",
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
    prompt_version: str = "template-v1",
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
