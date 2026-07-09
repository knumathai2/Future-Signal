"""Local development seeding script for related events.

Inserts manually curated context events for 4 representative normalized issues:
1. Kraken IPO
2. UK Election
3. NATO membership
4. OpenAI hardware

Safety Guidelines Compliance:
- Every event note contains the required context disclaimer.
- No causal verbs (because, due to, caused by, triggered by) are used.
- No prohibited vocabulary from the project wording policy is used.
- Environment check ensures this only writes in local development.
"""

import argparse
import logging
import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Market, MarketOutcome, RelatedEvent
from app.db.session import get_session_factory

logger = logging.getLogger(__name__)

# Allowed environments for safety guardrails
ALLOWED_WRITE_ENVS = {"local", "dev", "development", "test"}

CONTEXT_NOTE_SUFFIX = (
    "Candidate context entered manually for review alongside the observed change; "
    "not presented as a cause."
)

# Curated issues list with stable IDs and their related events
CURATED_SEED_DATA = [
    {
        "id": uuid.UUID("c3d4e5f6-0000-4000-8000-000000000003"),
        "polymarket_condition_id": (
            "0xced0cb8725bad43d78fda0cd0e5fa9e31804625cb3502b2c7897f8e8f7fa9e1f"
        ),
        "title": "Kraken IPO by December 31, 2026?",
        "description": (
            "Tracks reflected expectation in public prediction-market data for this "
            "crypto issue. Interpret changes with caution and verify source context."
        ),
        "category": "Crypto",
        "outcome_label": "Yes",
        "token_id": (
            "34626184950254225208692030156208941308358060420950772251072421141618169142241"
        ),
        "events": [
            {
                "id": uuid.UUID("e3f1c2a4-0000-4000-8000-000000000001"),
                "event_title": "Kraken Files Initial Registration Statement Draft",
                "event_date": datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC),
                "note": (
                    "A draft registration statement was submitted. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
            {
                "id": uuid.UUID("e3f1c2a4-0000-4000-8000-000000000002"),
                "event_title": "Major Crypto Exchange Regulatory Review Update",
                "event_date": datetime(2026, 5, 5, 8, 30, 0, tzinfo=UTC),
                "note": (
                    "Regulatory body published updated guidance on compliance metrics. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
        ],
    },
    {
        "id": uuid.UUID("d4e5f6a7-0000-4000-8000-000000000004"),
        "polymarket_condition_id": (
            "0x43204573cf724eda06c520a42a7cb97df319cc27ed997be3b96ca74398ede87f"
        ),
        "title": "Will the next UK election be called by December 31, 2026?",
        "description": (
            "Tracks reflected expectation in public prediction-market data for this UK "
            "issue. Interpret changes with caution and verify source context."
        ),
        "category": "UK",
        "outcome_label": "Yes",
        "token_id": (
            "31627048520492227354616069874124458767757243686332730237616510640600462926383"
        ),
        "events": [
            {
                "id": uuid.UUID("e4f1c2a4-0000-4000-8000-000000000001"),
                "event_title": "Prime Minister Addresses Parliamentary Session",
                "event_date": datetime(2026, 4, 14, 15, 0, 0, tzinfo=UTC),
                "note": (
                    "Speech discussing upcoming legislative agendas. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
            {
                "id": uuid.UUID("e4f1c2a4-0000-4000-8000-000000000002"),
                "event_title": "Local Council Election Initial Results Declared",
                "event_date": datetime(2026, 5, 8, 1, 0, 0, tzinfo=UTC),
                "note": (
                    "Voters participated in local administrative elections across regions. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
        ],
    },
    {
        "id": uuid.UUID("e5f6a7b8-0000-4000-8000-000000000005"),
        "polymarket_condition_id": (
            "0x523959b6256674318eb34755789fffd8c62cd652e5fa11ffd332402361d058e9"
        ),
        "title": "Will any country leave NATO by December 31, 2026?",
        "description": (
            "Tracks reflected expectation in public prediction-market data for this "
            "NATO issue. Interpret changes with caution and verify source context."
        ),
        "category": "NATO",
        "outcome_label": "Yes",
        "token_id": (
            "97672112380588518658859221422581522664938121648778223046012006536512218182756"
        ),
        "events": [
            {
                "id": uuid.UUID("e5f1c2a4-0000-4000-8000-000000000001"),
                "event_title": "NATO Foreign Ministers Meeting Coverage",
                "event_date": datetime(2026, 4, 3, 16, 0, 0, tzinfo=UTC),
                "note": (
                    "Public coverage reviewed alliance coordination topics. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
            {
                "id": uuid.UUID("e5f1c2a4-0000-4000-8000-000000000002"),
                "event_title": "Defense Spending Policy Statements Published",
                "event_date": datetime(2026, 6, 12, 11, 0, 0, tzinfo=UTC),
                "note": (
                    "Member-state policy statements discussed defense spending plans. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
        ],
    },
    {
        "id": uuid.UUID("f6a7b8c9-0000-4000-8000-000000000006"),
        "polymarket_condition_id": (
            "0xf53d2cf86bf4ea3c6a0bfb739cc0dded28001dde6eee5f90b8bb6716ce33571a"
        ),
        "title": "Will OpenAI launch a new consumer hardware product by December 31, 2026?",
        "description": (
            "Tracks reflected expectation in public prediction-market data for this "
            "tech issue. Interpret changes with caution and verify source context."
        ),
        "category": "Tech",
        "outcome_label": "Yes",
        "token_id": (
            "108052633825118494550832240247980096965299835115818656939682823516952479310001"
        ),
        "events": [
            {
                "id": uuid.UUID("e6f1c2a4-0000-4000-8000-000000000001"),
                "event_title": "Consumer Device Roadmap Discussion",
                "event_date": datetime(2026, 2, 4, 18, 0, 0, tzinfo=UTC),
                "note": (
                    "Public discussion referenced consumer device roadmap questions. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
            {
                "id": uuid.UUID("e6f1c2a4-0000-4000-8000-000000000002"),
                "event_title": "Hardware Partnership Context Review",
                "event_date": datetime(2026, 5, 21, 13, 0, 0, tzinfo=UTC),
                "note": (
                    "Public context review covered hardware partnership themes. "
                    f"{CONTEXT_NOTE_SUFFIX}"
                ),
            },
        ],
    },
]


def ensure_local_dev_write_allowed(env: str, confirmed: bool) -> None:
    """Hard guard for the related events seed CLI write path."""
    if not confirmed:
        raise RuntimeError(
            "Refusing to write related events seed rows without "
            "--confirm-local-dev-write."
        )
    if env.lower() not in ALLOWED_WRITE_ENVS:
        raise RuntimeError(
            f"Refusing related events seed writes when ENV={env!r}. Allowed values: "
            f"{', '.join(sorted(ALLOWED_WRITE_ENVS))}."
        )


def seed_related_events(db: Session) -> int:
    """Seeds markets (if missing) and inserts manually curated related events."""
    now = datetime.now(UTC)
    total_events_inserted = 0

    for data in CURATED_SEED_DATA:
        # 1. Look up or insert market
        market = db.execute(
            select(Market).where(
                Market.polymarket_condition_id == data["polymarket_condition_id"]
            )
        ).scalar_one_or_none()

        if market is None:
            logger.info("Market not found. Creating market: %s", data["title"])
            market = Market(
                id=data["id"],
                polymarket_condition_id=data["polymarket_condition_id"],
                title=data["title"],
                description=data.get("description"),
                category=data["category"],
                outcome_type="binary",
                status="active",
                market_created_at=now,
                end_date=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(market)
            db.flush()
        else:
            logger.info("Market already exists: %s", market.title)

        # 2. Ensure outcome is tracked
        outcome = db.execute(
            select(MarketOutcome).where(
                MarketOutcome.market_id == market.id, MarketOutcome.is_tracked.is_(True)
            )
        ).scalar_one_or_none()

        if outcome is None:
            outcome = MarketOutcome(
                id=uuid.uuid4(),
                market_id=market.id,
                outcome_label=data["outcome_label"],
                token_id=data.get("token_id"),
                is_tracked=True,
            )
            db.add(outcome)
            db.flush()

        # 3. Clean up existing related events for this market to ensure idempotency
        db.execute(delete(RelatedEvent).where(RelatedEvent.market_id == market.id))
        db.flush()

        # 4. Insert curated related events
        for event_data in data["events"]:
            related_event = RelatedEvent(
                id=event_data["id"],
                market_id=market.id,
                event_title=event_data["event_title"],
                event_date=event_data["event_date"],
                note=event_data["note"],
            )
            db.add(related_event)
            total_events_inserted += 1

    db.commit()
    logger.info(
        "Successfully seeded related events. Total events inserted: %d",
        total_events_inserted,
    )
    return total_events_inserted


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed manually curated related events.")
    parser.add_argument(
        "--confirm-local-dev-write",
        action="store_true",
        help="Required before this command writes to the configured local/dev DB.",
    )
    return parser


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    args = build_arg_parser().parse_args()

    try:
        ensure_local_dev_write_allowed(settings.env, args.confirm_local_dev_write)
    except RuntimeError as err:
        logger.error(str(err))
        return 1

    if not settings.database_url:
        logger.error("DATABASE_URL is not set.")
        return 1

    session = get_session_factory()()
    try:
        seed_related_events(session)
    except Exception as err:
        logger.exception("Failed to seed related events: %s", str(err))
        return 1
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
