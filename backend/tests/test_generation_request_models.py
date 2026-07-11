"""TASK-102 append-only request/event schema contract tests."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateTable

from app.db.models import (
    AiReport,
    AiReportGenerationBlock,
    AiReportGenerationEvent,
    AiReportGenerationRequest,
    Base,
    Market,
    MarketMetric,
)

NOW = datetime(2026, 7, 11, 10, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
REQUEST_ID = uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
REPORT_ID = uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
FINGERPRINT = hashlib.sha256(b"v7-input").hexdigest()
MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            Market.__table__,
            MarketMetric.__table__,
            AiReport.__table__,
            AiReportGenerationRequest.__table__,
            AiReportGenerationEvent.__table__,
            AiReportGenerationBlock.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    session.add(
        Market(
            id=MARKET_ID,
            polymarket_condition_id="condition-v7-request",
            title="Will the documented condition be confirmed?",
            description="Local request-schema fixture.",
            category="technology",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=2),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=2),
            last_seen_at=NOW,
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _request(**overrides) -> AiReportGenerationRequest:
    values = {
        "id": REQUEST_ID,
        "market_id": MARKET_ID,
        "input_fingerprint": FINGERPRINT,
        "prompt_version": "v7",
        "policy_version": "v7-positive-evidence-1",
        "input_schema_version": "v7-writer-input-1",
        "requested_by": "user",
        "context_refresh_requested": False,
        "input_evidence_refs": ["market_definition:r1", "metric:42"],
        "requested_at": NOW,
    }
    values.update(overrides)
    return AiReportGenerationRequest(**values)


def _event(event_id: int, state: str, **overrides) -> AiReportGenerationEvent:
    values = {
        "id": event_id,
        "request_id": REQUEST_ID,
        "state": state,
        "attempt_number": 0 if state == "queued" else 1,
        "recorded_at": NOW + timedelta(seconds=event_id),
        "lease_token": None,
        "lease_expires_at": None,
        "report_id": None,
        "error_code": None,
        "usage": {},
    }
    if state == "running":
        values.update(
            lease_token=uuid.UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            lease_expires_at=NOW + timedelta(minutes=5),
        )
    elif state == "succeeded":
        values["report_id"] = REPORT_ID
    elif state == "failed":
        values["error_code"] = "provider_unavailable"
    values.update(overrides)
    return AiReportGenerationEvent(**values)


def _block(block_id: int, sequence: int = 0, **overrides) -> AiReportGenerationBlock:
    values = {
        "id": block_id,
        "request_id": REQUEST_ID,
        "attempt_number": 1,
        "sequence_number": sequence,
        "block_type": "headline_summary" if sequence == 0 else "section",
        "payload": {"kind": "headline_summary" if sequence == 0 else "section"},
        "recorded_at": NOW + timedelta(seconds=block_id),
    }
    values.update(overrides)
    return AiReportGenerationBlock(**values)


def test_request_and_event_history_are_append_only_and_ordered(db):
    db.add(_request())
    db.commit()
    db.add_all([_event(1, "queued"), _event(2, "running"), _event(3, "failed")])
    db.commit()

    events = (
        db.query(AiReportGenerationEvent)
        .filter_by(request_id=REQUEST_ID)
        .order_by(AiReportGenerationEvent.id)
        .all()
    )
    assert [item.state for item in events] == ["queued", "running", "failed"]


def test_same_market_and_fingerprint_is_idempotent(db):
    db.add(_request())
    db.commit()
    db.add(_request(id=uuid.uuid4()))

    with pytest.raises(IntegrityError):
        db.commit()


def test_validated_block_sequence_is_unique_per_request_attempt(db):
    db.add(_request())
    db.commit()
    db.add(_block(1))
    db.commit()
    db.add(_block(2))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize(
    "event_row",
    [
        _event(1, "running", lease_token=None),
        _event(2, "succeeded", report_id=None),
        _event(3, "failed", error_code=None),
        _event(4, "queued", lease_token=uuid.uuid4()),
    ],
)
def test_event_shape_rejects_incomplete_or_mixed_states(db, event_row):
    db.add(_request())
    db.add(event_row)
    with pytest.raises(IntegrityError):
        db.commit()


def test_succeeded_event_requires_existing_report(db):
    db.add(_request())
    db.commit()
    db.add(_event(1, "succeeded"))
    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()
    db.add(
        AiReport(
            id=REPORT_ID,
            market_id=MARKET_ID,
            generated_at=NOW,
            input_metrics_id=None,
            content={},
            model_used="fake/model",
            prompt_version="v7",
            status="success",
        )
    )
    db.add(_event(2, "succeeded"))
    db.commit()
    assert db.query(AiReportGenerationEvent).one().report_id == REPORT_ID


def test_parent_request_and_market_cascade_operational_history(db):
    db.add(_request())
    db.commit()
    db.add(_event(1, "queued"))
    db.add(_block(1))
    db.commit()

    db.delete(db.get(Market, MARKET_ID))
    db.commit()
    assert db.query(AiReportGenerationRequest).count() == 0
    assert db.query(AiReportGenerationEvent).count() == 0
    assert db.query(AiReportGenerationBlock).count() == 0


def test_postgres_ddl_has_jsonb_timezone_fks_and_named_indexes():
    request_ddl = str(
        CreateTable(AiReportGenerationRequest.__table__).compile(dialect=postgresql.dialect())
    )
    event_ddl = str(
        CreateTable(AiReportGenerationEvent.__table__).compile(dialect=postgresql.dialect())
    )
    block_ddl = str(
        CreateTable(AiReportGenerationBlock.__table__).compile(dialect=postgresql.dialect())
    )
    assert "JSONB NOT NULL" in request_ddl
    assert "TIMESTAMP WITH TIME ZONE NOT NULL" in request_ddl
    assert "JSONB NOT NULL" in event_ddl
    assert "ON DELETE CASCADE" in event_ddl
    assert "ON DELETE SET NULL" in event_ddl
    assert "JSONB NOT NULL" in block_ddl
    assert "ON DELETE CASCADE" in block_ddl
    assert {index.name for index in AiReportGenerationRequest.__table__.indexes} == {
        "idx_ai_report_generation_requests_market_requested"
    }
    assert {index.name for index in AiReportGenerationEvent.__table__.indexes} == {
        "idx_ai_report_generation_events_request_recorded"
    }
    assert {index.name for index in AiReportGenerationBlock.__table__.indexes} == {
        "idx_ai_report_generation_blocks_request_attempt_sequence"
    }


def test_migration_is_additive_and_does_not_edit_prior_migrations():
    migration = (MIGRATIONS / "004_ai_report_generation_requests.sql").read_text()
    initial = (MIGRATIONS / "001_initial_schema.sql").read_text()
    assert "CREATE TABLE ai_report_generation_requests" in migration
    assert "CREATE TABLE ai_report_generation_events" in migration
    assert "UNIQUE (market_id, input_fingerprint)" in migration
    assert "UPDATE " not in migration
    assert "DELETE FROM" not in migration
    assert "ai_report_generation_requests" not in initial
    assert "ai_report_generation_events" not in initial
    block_migration = (MIGRATIONS / "005_ai_report_generation_blocks.sql").read_text()
    assert "CREATE TABLE ai_report_generation_blocks" in block_migration
    assert "UNIQUE (request_id, attempt_number, sequence_number)" in block_migration
    assert "UPDATE " not in block_migration
    assert "DELETE FROM" not in block_migration
