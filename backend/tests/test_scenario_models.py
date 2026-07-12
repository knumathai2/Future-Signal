"""TASK-126 scenario migration and ORM contract tests."""

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
    Base,
    Market,
    ScenarioGenerationEvent,
    ScenarioGenerationRequest,
    ScenarioPremise,
    ScenarioResponseBlock,
    ScenarioSession,
    ScenarioTurn,
)

NOW = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
SESSION_ID = uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
TURN_ID = uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
REQUEST_ID = uuid.UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
ASSISTANT_TURN_ID = uuid.UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
FINGERPRINT = hashlib.sha256(b"scenario-input").hexdigest()
CAPABILITY_HASH = hashlib.sha256(b"capability").hexdigest()
IDEMPOTENCY_HASH = hashlib.sha256(b"idempotency").hexdigest()
MIGRATION = Path(__file__).resolve().parents[1] / "migrations/006_scenario_conversations.sql"


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
            ScenarioSession.__table__,
            ScenarioTurn.__table__,
            ScenarioPremise.__table__,
            ScenarioGenerationRequest.__table__,
            ScenarioGenerationEvent.__table__,
            ScenarioResponseBlock.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    session.add(
        Market(
            id=MARKET_ID,
            polymarket_condition_id="scenario-condition",
            title="Will the documented condition be confirmed?",
            description="Scenario schema fixture.",
            category="technology",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=10),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=10),
            last_seen_at=NOW,
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _session(**overrides) -> ScenarioSession:
    values = {
        "id": SESSION_ID,
        "market_id": MARKET_ID,
        "capability_hash": CAPABILITY_HASH,
        "definition_ref": "market_definition:rule-1",
        "input_fingerprint": FINGERPRINT,
        "policy_version": "summary-scenario-policy-1",
        "input_schema_version": "scenario-session-input-1",
        "data_as_of": NOW,
        "caution_note": "A sufficiently long deterministic caution statement for tests.",
        "max_turns": 8,
        "created_at": NOW,
        "expires_at": NOW + timedelta(hours=24),
    }
    values.update(overrides)
    return ScenarioSession(**values)


def _turn(**overrides) -> ScenarioTurn:
    values = {
        "id": TURN_ID,
        "session_id": SESSION_ID,
        "sequence_number": 1,
        "role": "user",
        "content": "Explore one conditional path.",
        "idempotency_key_hash": IDEMPOTENCY_HASH,
        "created_at": NOW,
    }
    values.update(overrides)
    return ScenarioTurn(**values)


def _request(**overrides) -> ScenarioGenerationRequest:
    values = {
        "id": REQUEST_ID,
        "session_id": SESSION_ID,
        "user_turn_id": TURN_ID,
        "input_fingerprint": FINGERPRINT,
        "policy_version": "summary-scenario-policy-1",
        "input_schema_version": "scenario-session-input-1",
        "input_premise_refs": [],
        "requested_at": NOW,
    }
    values.update(overrides)
    return ScenarioGenerationRequest(**values)


def _event(event_id: int, state: str, **overrides) -> ScenarioGenerationEvent:
    values = {
        "id": event_id,
        "request_id": REQUEST_ID,
        "session_id": SESSION_ID,
        "state": state,
        "attempt_number": 0 if state == "queued" else 1,
        "recorded_at": NOW + timedelta(seconds=event_id),
        "lease_token": None,
        "lease_expires_at": None,
        "assistant_turn_id": None,
        "error_code": None,
        "usage": {},
    }
    if state == "running":
        values.update(
            lease_token=uuid.uuid4(),
            lease_expires_at=NOW + timedelta(minutes=5),
        )
    elif state == "succeeded":
        values["assistant_turn_id"] = ASSISTANT_TURN_ID
    elif state == "failed":
        values["error_code"] = "generation_unavailable"
    values.update(overrides)
    return ScenarioGenerationEvent(**values)


def _seed_request(db) -> None:
    db.add(_session())
    db.commit()
    db.add(_turn())
    db.commit()
    db.add(_request())
    db.commit()


def test_scenario_rows_enforce_fixed_session_and_append_only_shapes(db):
    _seed_request(db)
    db.add_all([_event(1, "queued"), _event(2, "running"), _event(3, "failed")])
    db.commit()

    assert [
        row.state
        for row in db.query(ScenarioGenerationEvent)
        .order_by(ScenarioGenerationEvent.id)
        .all()
    ] == ["queued", "running", "failed"]


@pytest.mark.parametrize(
    "row",
    [
        _session(max_turns=9),
        _session(expires_at=NOW),
    ],
)
def test_session_shape_rejects_expanded_or_invalid_lifetime(db, row):
    db.add(row)
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize(
    "row",
    [
        _turn(role="assistant", idempotency_key_hash=IDEMPOTENCY_HASH),
        _turn(content="x" * 1001),
        _turn(sequence_number=0),
    ],
)
def test_turn_shape_rejects_invalid_role_content_or_sequence(db, row):
    db.add(_session())
    db.commit()
    db.add(row)
    with pytest.raises(IntegrityError):
        db.commit()


def test_premise_class_cannot_leave_the_approved_enum(db):
    db.add(_session())
    db.commit()
    db.add(_turn())
    db.commit()
    db.add(
        ScenarioPremise(
            id=uuid.uuid4(),
            session_id=SESSION_ID,
            premise_class="promoted_fact",
            text="Invalid class.",
            origin_turn_id=TURN_ID,
            evidence_refs=[],
            created_at=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_cross_session_premise_and_assistant_links_are_rejected(db):
    _seed_request(db)
    other_session_id = uuid.uuid4()
    other_turn_id = uuid.uuid4()
    db.add(
        _session(
            id=other_session_id,
            capability_hash=hashlib.sha256(b"other-capability").hexdigest(),
        )
    )
    db.commit()
    db.add(
        _turn(
            id=other_turn_id,
            session_id=other_session_id,
            idempotency_key_hash=hashlib.sha256(b"other-idempotency").hexdigest(),
        )
    )
    db.commit()

    db.add(
        ScenarioPremise(
            id=uuid.uuid4(),
            session_id=SESSION_ID,
            premise_class="user_assumption",
            text="Cross-session premise.",
            origin_turn_id=other_turn_id,
            evidence_refs=[],
            created_at=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(_event(1, "succeeded", assistant_turn_id=other_turn_id))
    with pytest.raises(IntegrityError):
        db.commit()


def test_event_and_block_shapes_fail_closed(db):
    _seed_request(db)
    db.add(_event(1, "running", lease_token=None))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(
        ScenarioResponseBlock(
            id=1,
            request_id=REQUEST_ID,
            attempt_number=1,
            sequence_number=0,
            block_type="raw_token",
            payload={},
            recorded_at=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_session_delete_cascades_only_the_ephemeral_graph(db):
    _seed_request(db)
    db.add(_event(1, "queued"))
    db.add(
        ScenarioResponseBlock(
            id=1,
            request_id=REQUEST_ID,
            attempt_number=1,
            sequence_number=0,
            block_type="paragraph",
            payload={"text": "Validated paragraph."},
            recorded_at=NOW,
        )
    )
    db.commit()

    db.delete(db.get(ScenarioSession, SESSION_ID))
    db.commit()

    assert db.get(Market, MARKET_ID) is not None
    assert db.query(ScenarioTurn).count() == 0
    assert db.query(ScenarioGenerationRequest).count() == 0
    assert db.query(ScenarioGenerationEvent).count() == 0
    assert db.query(ScenarioResponseBlock).count() == 0


def test_postgres_ddl_and_migration_keep_security_constraints():
    session_ddl = str(CreateTable(ScenarioSession.__table__).compile(dialect=postgresql.dialect()))
    request_ddl = str(
        CreateTable(ScenarioGenerationRequest.__table__).compile(
            dialect=postgresql.dialect()
        )
    )
    block_ddl = str(
        CreateTable(ScenarioResponseBlock.__table__).compile(dialect=postgresql.dialect())
    )
    migration = MIGRATION.read_text()

    assert "TIMESTAMP WITH TIME ZONE NOT NULL" in session_ddl
    assert "capability_hash" in session_ddl
    assert "JSONB NOT NULL" in request_ddl
    assert "scenario_response_blocks" in block_ddl
    assert "CREATE TABLE scenario_sessions" in migration
    assert "capability_hash ~ '^[0-9a-f]{64}$'" in migration
    assert "max_turns = 8" in migration
    assert "ON DELETE CASCADE" in migration
    assert "block_type IN ('paragraph', 'list')" in migration
