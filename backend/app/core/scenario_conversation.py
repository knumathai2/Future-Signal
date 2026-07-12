"""Capability-scoped, provider-free scenario conversation state.

TASK-126 implements only the append-only session/turn/request boundary and
ephemeral cleanup. This module never constructs an AI client or calls an
external service.
"""

import hashlib
import secrets
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.ai_report import build_caution_note
from app.core.on_demand_briefing import build_v8_input_bundle, v8_input_fingerprint
from app.db.models import (
    ScenarioGenerationEvent,
    ScenarioGenerationRequest,
    ScenarioPremise,
    ScenarioResponseBlock,
    ScenarioSession,
    ScenarioTurn,
)

SCENARIO_POLICY_VERSION = "summary-scenario-policy-1"
SCENARIO_INPUT_SCHEMA_VERSION = "scenario-session-input-1"
SCENARIO_SESSION_LIFETIME = timedelta(hours=24)
SCENARIO_MAX_TURNS = 8
SCENARIO_MAX_MESSAGE_CHARS = 1_000
SCENARIO_MAX_RESPONSE_CHARS = 2_500
SCENARIO_MAX_CONVERSATION_CHARS = 20_000


class ScenarioUnavailableError(ValueError):
    """The requested session cannot be disclosed or used by this caller."""


class ScenarioStateError(ValueError):
    """The authenticated session cannot accept the requested transition."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CreatedScenarioSession:
    session: ScenarioSession
    capability: str


@dataclass(frozen=True)
class EnqueuedScenarioTurn:
    request: ScenarioGenerationRequest
    turn: ScenarioTurn
    created: bool


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def hash_secret(value: str) -> str:
    """Hash a high-entropy capability or idempotency key for storage."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_session_capability() -> str:
    """Return 256 bits of URL-safe random material."""
    return secrets.token_urlsafe(32)


def normalize_scenario_message(value: str) -> str:
    """Normalize compatibility forms and reject hidden control characters."""
    normalized = unicodedata.normalize("NFKC", value).strip()
    if any(
        unicodedata.category(character).startswith("C") and character not in {"\n", "\t"}
        for character in normalized
    ):
        raise ScenarioStateError("invalid_request")
    return normalized


def latest_scenario_event(
    db: Session,
    request_id: uuid.UUID,
) -> ScenarioGenerationEvent | None:
    return db.execute(
        select(ScenarioGenerationEvent)
        .where(ScenarioGenerationEvent.request_id == request_id)
        .order_by(
            ScenarioGenerationEvent.recorded_at.desc(),
            ScenarioGenerationEvent.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def create_scenario_session(
    db: Session,
    market_id: uuid.UUID,
    *,
    now: datetime | None = None,
    capability: str | None = None,
) -> CreatedScenarioSession | None:
    """Create one fixed-expiry session over the current reconstructible bundle."""
    created_at = _as_utc(now or datetime.now(UTC))
    bundle = build_v8_input_bundle(db, market_id, now=created_at)
    if bundle is None:
        return None
    raw_capability = capability or generate_session_capability()
    caution_note = build_caution_note(bundle.confidence_level)
    if caution_note is None:
        return None
    session = ScenarioSession(
        id=uuid.uuid4(),
        market_id=market_id,
        capability_hash=hash_secret(raw_capability),
        definition_ref=bundle.definition_ref,
        input_fingerprint=v8_input_fingerprint(bundle),
        policy_version=SCENARIO_POLICY_VERSION,
        input_schema_version=SCENARIO_INPUT_SCHEMA_VERSION,
        data_as_of=bundle.data_as_of,
        caution_note=caution_note,
        max_turns=SCENARIO_MAX_TURNS,
        created_at=created_at,
        expires_at=created_at + SCENARIO_SESSION_LIFETIME,
    )
    db.add(session)
    db.commit()
    return CreatedScenarioSession(session=session, capability=raw_capability)


def authenticate_scenario_session(
    db: Session,
    market_id: uuid.UUID,
    session_id: uuid.UUID,
    capability: str,
    *,
    now: datetime | None = None,
) -> ScenarioSession:
    """Authenticate without revealing whether identity, scope, or expiry failed."""
    session = db.get(ScenarioSession, session_id)
    current_time = _as_utc(now or datetime.now(UTC))
    if (
        session is None
        or session.market_id != market_id
        or _as_utc(session.expires_at) <= current_time
        or not secrets.compare_digest(session.capability_hash, hash_secret(capability))
    ):
        raise ScenarioUnavailableError("session_unavailable")
    return session


def _active_request_exists(db: Session, session_id: uuid.UUID) -> bool:
    request_ids = db.execute(
        select(ScenarioGenerationRequest.id).where(
            ScenarioGenerationRequest.session_id == session_id
        )
    ).scalars()
    return any(
        (event := latest_scenario_event(db, request_id)) is not None
        and event.state in {"queued", "running"}
        for request_id in request_ids
    )


def enqueue_scenario_turn(
    db: Session,
    session: ScenarioSession,
    message: str,
    idempotency_key: str,
    *,
    now: datetime | None = None,
) -> EnqueuedScenarioTurn:
    """Append one user turn, immutable request, and queued event atomically."""
    requested_at = _as_utc(now or datetime.now(UTC))
    if _as_utc(session.expires_at) <= requested_at:
        raise ScenarioUnavailableError("session_unavailable")
    normalized_message = normalize_scenario_message(message)
    if not 1 <= len(normalized_message) <= SCENARIO_MAX_MESSAGE_CHARS:
        raise ScenarioStateError("message_too_large")
    idempotency_hash = hash_secret(idempotency_key)
    existing_turn = db.execute(
        select(ScenarioTurn).where(
            ScenarioTurn.session_id == session.id,
            ScenarioTurn.idempotency_key_hash == idempotency_hash,
        )
    ).scalar_one_or_none()
    if existing_turn is not None:
        existing_request = db.execute(
            select(ScenarioGenerationRequest).where(
                ScenarioGenerationRequest.user_turn_id == existing_turn.id
            )
        ).scalar_one()
        return EnqueuedScenarioTurn(
            request=existing_request,
            turn=existing_turn,
            created=False,
        )

    current_bundle = build_v8_input_bundle(db, session.market_id, now=requested_at)
    if current_bundle is None or v8_input_fingerprint(current_bundle) != session.input_fingerprint:
        raise ScenarioStateError("session_stale")

    user_turn_count = db.execute(
        select(func.count(ScenarioTurn.id)).where(
            ScenarioTurn.session_id == session.id,
            ScenarioTurn.role == "user",
        )
    ).scalar_one()
    if user_turn_count >= session.max_turns:
        raise ScenarioStateError("session_limit_reached")
    conversation_chars = db.execute(
        select(func.coalesce(func.sum(func.length(ScenarioTurn.content)), 0)).where(
            ScenarioTurn.session_id == session.id
        )
    ).scalar_one()
    if int(conversation_chars) + len(normalized_message) > SCENARIO_MAX_CONVERSATION_CHARS:
        raise ScenarioStateError("session_limit_reached")
    if _active_request_exists(db, session.id):
        raise ScenarioStateError("turn_in_progress")

    last_sequence = db.execute(
        select(func.coalesce(func.max(ScenarioTurn.sequence_number), 0)).where(
            ScenarioTurn.session_id == session.id
        )
    ).scalar_one()
    sequence_number = int(last_sequence) + 1
    turn = ScenarioTurn(
        id=uuid.uuid4(),
        session_id=session.id,
        sequence_number=sequence_number,
        role="user",
        content=normalized_message,
        idempotency_key_hash=idempotency_hash,
        created_at=requested_at,
    )
    premise_refs = [
        str(value)
        for value in db.execute(
            select(ScenarioPremise.id)
            .where(ScenarioPremise.session_id == session.id)
            .order_by(ScenarioPremise.created_at.asc(), ScenarioPremise.id.asc())
        ).scalars()
    ]
    request_fingerprint = hashlib.sha256(
        "\x1f".join(
            [
                session.input_fingerprint,
                str(sequence_number),
                normalized_message,
                *premise_refs,
                SCENARIO_POLICY_VERSION,
                SCENARIO_INPUT_SCHEMA_VERSION,
            ]
        ).encode("utf-8")
    ).hexdigest()
    request = ScenarioGenerationRequest(
        id=uuid.uuid4(),
        session_id=session.id,
        user_turn_id=turn.id,
        input_fingerprint=request_fingerprint,
        policy_version=SCENARIO_POLICY_VERSION,
        input_schema_version=SCENARIO_INPUT_SCHEMA_VERSION,
        input_premise_refs=premise_refs,
        requested_at=requested_at,
    )
    event = ScenarioGenerationEvent(
        request_id=request.id,
        session_id=session.id,
        state="queued",
        attempt_number=0,
        recorded_at=requested_at,
        lease_token=None,
        lease_expires_at=None,
        assistant_turn_id=None,
        error_code=None,
        usage={},
    )
    # Composite same-session FKs intentionally do not rely on ORM relationship
    # objects. Flush the parent rows explicitly so Postgres cannot schedule the
    # queued event before its request within the same unit of work.
    db.add(turn)
    db.flush([turn])
    db.add(request)
    db.flush([request])
    db.add(event)
    db.commit()
    return EnqueuedScenarioTurn(request=request, turn=turn, created=True)


def delete_scenario_session(
    db: Session,
    session: ScenarioSession,
) -> None:
    """Hard-delete only the authenticated ephemeral conversation graph."""
    _delete_scenario_graph(db, session.id)
    db.commit()


def _delete_scenario_graph(db: Session, session_id: uuid.UUID) -> None:
    """Delete children explicitly so SQLite tests mirror Postgres cascades."""
    request_ids = select(ScenarioGenerationRequest.id).where(
        ScenarioGenerationRequest.session_id == session_id
    )
    db.execute(
        delete(ScenarioResponseBlock).where(
            ScenarioResponseBlock.request_id.in_(request_ids)
        )
    )
    db.execute(
        delete(ScenarioGenerationEvent).where(
            ScenarioGenerationEvent.request_id.in_(request_ids)
        )
    )
    db.execute(
        delete(ScenarioPremise).where(ScenarioPremise.session_id == session_id)
    )
    db.execute(
        delete(ScenarioGenerationRequest).where(
            ScenarioGenerationRequest.session_id == session_id
        )
    )
    db.execute(delete(ScenarioTurn).where(ScenarioTurn.session_id == session_id))
    db.execute(delete(ScenarioSession).where(ScenarioSession.id == session_id))


def cleanup_expired_scenario_sessions(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    """Delete expired ephemeral graphs; never touch market/report history."""
    current_time = _as_utc(now or datetime.now(UTC))
    sessions = list(
        db.execute(
            select(ScenarioSession).where(ScenarioSession.expires_at <= current_time)
        ).scalars()
    )
    for session in sessions:
        _delete_scenario_graph(db, session.id)
    db.commit()
    return len(sessions)
