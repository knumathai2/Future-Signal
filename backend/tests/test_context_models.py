"""TASK-057 schema and ORM contract tests.

The suite uses an in-memory SQLite database only. It validates the accepted
Postgres migration text and SQLAlchemy metadata without applying either schema
to the configured development or production database.
"""

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

from app.db.models import Base, ContextCandidate, ContextCollectionRun, Market

NOW = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
MARKET_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
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
            ContextCandidate.__table__,
            ContextCollectionRun.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    session.add(
        Market(
            id=MARKET_ID,
            polymarket_condition_id="condition-context-test",
            title="Will the documented condition be confirmed?",
            description="A local schema test issue.",
            category="technology",
            outcome_type="binary",
            status="active",
            market_created_at=NOW - timedelta(days=30),
            end_date=NOW + timedelta(days=30),
            first_seen_at=NOW - timedelta(days=30),
            last_seen_at=NOW,
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _candidate(**overrides) -> ContextCandidate:
    values = {
        "id": uuid.uuid4(),
        "market_id": MARKET_ID,
        "episode_at": NOW,
        "event_title": "Official update recorded in the review window",
        "event_at": NOW - timedelta(hours=1),
        "neutral_summary": "An official source recorded an update in the review window.",
        "sources": [
            {
                "title": "Official source",
                "url": "https://example.gov/update",
                "domain": "example.gov",
                "source_type": "official",
            }
        ],
        "verification_state": "verified",
        "verification_score_internal": 0.95,
        "research_model": "research/model-a",
        "verifier_model": "verify/model-b",
        "policy_version": "v4",
        "evidence_hash": "sha256:evidence-1",
        "collected_at": NOW,
        "expires_at": NOW + timedelta(hours=24),
    }
    values.update(overrides)
    return ContextCandidate(**values)


def _run(**overrides) -> ContextCollectionRun:
    values = {
        "id": uuid.uuid4(),
        "market_id": MARKET_ID,
        "episode_at": NOW,
        "started_at": NOW,
        "finished_at": NOW + timedelta(minutes=1),
        "status": "success",
        "query_count": 2,
        "result_count": 5,
        "accepted_count": 1,
        "model_usage": {
            "research_model": "research/model-a",
            "verifier_model": "verify/model-b",
            "input_tokens": 100,
            "output_tokens": 20,
            "web_searches": 2,
            "cost_usd": "0.05",
        },
        "error_detail": None,
    }
    values.update(overrides)
    return ContextCollectionRun(**values)


@pytest.mark.parametrize("state", ["verified", "withheld", "rejected"])
def test_candidate_allows_only_documented_states(db, state):
    db.add(_candidate(verification_state=state, evidence_hash=f"sha256:{state}"))
    db.commit()

    assert db.query(ContextCandidate).one().verification_state == state


def test_candidate_rejects_unknown_state(db):
    db.add(_candidate(verification_state="pending"))

    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("status", ["success", "partial", "failed", "no_candidate"])
def test_collection_run_allows_only_documented_statuses(db, status):
    db.add(_run(status=status))
    db.commit()

    assert db.query(ContextCollectionRun).one().status == status


def test_collection_run_rejects_unknown_status_and_negative_counts(db):
    db.add(_run(status="pending"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(_run(query_count=-1))
    with pytest.raises(IntegrityError):
        db.commit()


def test_duplicate_evidence_is_idempotent_per_market_episode(db):
    db.add(_candidate())
    db.commit()
    db.add(_candidate())

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(_candidate(episode_at=NOW + timedelta(hours=1)))
    db.commit()
    assert db.query(ContextCandidate).count() == 2


def test_parent_market_delete_cascades_to_context_rows(db):
    db.add(_candidate())
    db.add(_run())
    db.commit()

    db.delete(db.get(Market, MARKET_ID))
    db.commit()

    assert db.query(ContextCandidate).count() == 0
    assert db.query(ContextCollectionRun).count() == 0


def test_metadata_exposes_expected_indexes_constraints_and_secret_free_fields():
    candidate = ContextCandidate.__table__
    collection_run = ContextCollectionRun.__table__

    assert {index.name for index in candidate.indexes} == {
        "idx_context_candidates_market_episode_state"
    }
    assert {index.name for index in collection_run.indexes} == {
        "idx_context_collection_runs_market_episode"
    }
    assert next(iter(candidate.c.market_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(collection_run.c.market_id.foreign_keys)).ondelete == "CASCADE"

    all_columns = set(candidate.c.keys()) | set(collection_run.c.keys())
    assert all_columns.isdisjoint({"api_key", "prompt", "response"})


def test_models_compile_to_postgres_jsonb_and_timezone_aware_timestamps():
    candidate_ddl = str(
        CreateTable(ContextCandidate.__table__).compile(dialect=postgresql.dialect())
    )
    run_ddl = str(
        CreateTable(ContextCollectionRun.__table__).compile(dialect=postgresql.dialect())
    )

    assert "JSONB NOT NULL" in candidate_ddl
    assert "TIMESTAMP WITH TIME ZONE NOT NULL" in candidate_ddl
    assert "JSONB NOT NULL" in run_ddl
    assert "TIMESTAMP WITH TIME ZONE NOT NULL" in run_ddl


def test_migration_is_append_only_and_leaves_initial_schema_unchanged():
    migration = (MIGRATIONS / "002_context_candidates.sql").read_text()
    initial = (MIGRATIONS / "001_initial_schema.sql").read_text()

    assert "CREATE TABLE context_candidates" in migration
    assert "CREATE TABLE context_collection_runs" in migration
    assert "ON DELETE CASCADE" in migration
    assert "UNIQUE (market_id, episode_at, evidence_hash)" in migration
    assert "ALTER TABLE" not in migration
    assert "UPDATE " not in migration
    assert "DELETE FROM" not in migration
    assert "context_candidates" not in initial
    assert "context_collection_runs" not in initial
