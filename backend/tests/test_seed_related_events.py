"""Unit tests for the related events seeding script."""

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Market, MarketOutcome, RelatedEvent
from app.db.seed_related_events import (
    CURATED_SEED_DATA,
    ensure_local_dev_write_allowed,
    seed_related_events,
)
from app.core.config import settings
BANNED_WORDS = [
    "bet", "buy", "sell", "trade", "position", "long", "short", "profit",
    "win rate", "odds", "expert trader", "best pick", "recommended outcome",
    "high-return opportunity", "guaranteed prediction", "signal to act",
    "recommendation"
]

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


@pytest.fixture
def db_session():
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
            RelatedEvent.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_ensure_local_dev_write_allowed():
    # Should succeed under allowed envs and confirmed is True
    ensure_local_dev_write_allowed("local", True)
    ensure_local_dev_write_allowed("dev", True)
    ensure_local_dev_write_allowed("TEST", True)

    # Should raise error when confirmed is False
    with pytest.raises(RuntimeError, match="Refusing to write related events seed rows"):
        ensure_local_dev_write_allowed("local", False)

    # Should raise error when env is not allowed
    with pytest.raises(RuntimeError, match="Refusing related events seed writes when ENV="):
        ensure_local_dev_write_allowed("production", True)


def test_seed_related_events_success(db_session):
    # Execute the seed script
    inserted_count = seed_related_events(db_session)
    assert inserted_count > 0

    # Query markets and related events
    markets = db_session.query(Market).all()
    assert len(markets) == len(CURATED_SEED_DATA)

    related_events = db_session.query(RelatedEvent).all()
    assert len(related_events) == inserted_count

    # Verify that details match CURATED_SEED_DATA
    for data in CURATED_SEED_DATA:
        market = db_session.query(Market).filter_by(
            polymarket_condition_id=data["polymarket_condition_id"]
        ).one()
        assert market.id == data["id"]

        events = db_session.query(RelatedEvent).filter_by(market_id=market.id).all()
        assert len(events) == len(data["events"])

        # Check content safety for each event
        for event in events:
            # Note disclaimer check
            assert "Candidate context entered manually for review alongside the observed change; not presented as a cause." in event.note

            # Causal verbs check
            for causal_verb in ["because", "due to", "caused by", "triggered by"]:
                assert causal_verb not in event.note.lower()

            # Prohibited vocabulary check using word boundaries
            import re
            for word in BANNED_WORDS:
                pattern = r'\b' + re.escape(word).replace(r'\ ', r'\s+') + r'\b'
                assert not re.search(pattern, event.note.lower()), f"Found banned word '{word}' in note: {event.note}"


def test_seed_related_events_idempotency(db_session):
    # Running once
    count_1 = seed_related_events(db_session)
    # Running twice
    count_2 = seed_related_events(db_session)

    assert count_1 == count_2

    # Database count of related events must still equal count_1 (no duplicates)
    db_count = db_session.query(RelatedEvent).count()
    assert db_count == count_1
