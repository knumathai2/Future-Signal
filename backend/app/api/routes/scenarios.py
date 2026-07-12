"""Disabled-by-default, capability-scoped scenario conversation routes.

The API may append session/turn/request state. It never constructs a provider
client or launches a generation worker in TASK-126.
"""

import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.scenario_conversation import (
    ScenarioStateError,
    ScenarioUnavailableError,
    authenticate_scenario_session,
    create_scenario_session,
    delete_scenario_session,
    enqueue_scenario_turn,
    latest_scenario_event,
)
from app.core.scenario_worker_launcher import launch_scenario_worker
from app.db.models import (
    Market,
    ScenarioGenerationEvent,
    ScenarioGenerationRequest,
    ScenarioPremise,
    ScenarioResponseBlock,
    ScenarioSession,
    ScenarioTurn,
)
from app.db.session import get_db
from app.schemas.scenarios import (
    ScenarioPremiseOut,
    ScenarioSessionCreateResponse,
    ScenarioSessionResponse,
    ScenarioTurnCreateIn,
    ScenarioTurnCreateResponse,
    ScenarioTurnOut,
    ScenarioTurnStatusResponse,
)

router = APIRouter(tags=["scenario-conversations"])
_QUEUED_RELAUNCH_AFTER = timedelta(seconds=5)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _get_optional_db() -> Generator[Session | None, None, None]:
    if not settings.database_url:
        yield None
        return
    yield from get_db()


def _public_error(status_code: int, code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code},
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Vary": "Authorization, Origin",
        },
    )


def _set_private_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Vary"] = "Authorization, Origin"


def _ensure_enabled() -> None:
    if not settings.scenario_conversation_enabled or settings.env not in {
        "local",
        "development",
    }:
        raise _public_error(status.HTTP_404_NOT_FOUND, "feature_unavailable")


def _parse_capability(authorization: str | None) -> str:
    if authorization is None:
        raise _public_error(status.HTTP_401_UNAUTHORIZED, "session_token_required")
    scheme, separator, capability = authorization.partition(" ")
    capability = capability.strip()
    if (
        separator != " "
        or scheme.lower() != "bearer"
        or not 40 <= len(capability) <= 80
    ):
        raise _public_error(status.HTTP_401_UNAUTHORIZED, "session_token_required")
    return capability


class _LocalRateLimiter:
    """Process-local guard allowed only by the local/development feature gate."""

    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)
        self._events: dict[tuple[str, str, int], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def allow(self, client_key: str, kind: str, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        limits = (
            ((600, 3), (86400, 20))
            if kind == "session"
            else ((600, 10), (86400, 60))
        )
        digest = hmac.new(
            self._secret,
            client_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        with self._lock:
            buckets = []
            for seconds, maximum in limits:
                bucket = self._events[(digest, kind, seconds)]
                cutoff = timestamp - seconds
                while bucket and bucket[0] <= cutoff:
                    bucket.popleft()
                if len(bucket) >= maximum:
                    return False
                buckets.append(bucket)
            for bucket in buckets:
                bucket.append(timestamp)
            return True


_rate_limiter = _LocalRateLimiter()


def _client_key(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _authenticate(
    db: Session,
    issue_id: UUID,
    session_id: UUID,
    authorization: str | None,
) -> ScenarioSession:
    capability = _parse_capability(authorization)
    try:
        return authenticate_scenario_session(db, issue_id, session_id, capability)
    except ScenarioUnavailableError as exc:
        raise _public_error(status.HTTP_404_NOT_FOUND, "session_unavailable") from exc


def _turn_out(turn: ScenarioTurn) -> ScenarioTurnOut:
    return ScenarioTurnOut(
        turn_id=turn.id,
        sequence=turn.sequence_number,
        role=turn.role,
        content=turn.content,
        created_at=_as_utc(turn.created_at),
    )


def _maybe_relaunch_queued_request(
    generation_request: ScenarioGenerationRequest,
    latest: ScenarioGenerationEvent,
    *,
    now: datetime | None = None,
) -> bool:
    """Relaunch only an attempt-zero request that never reached provider work."""
    checked_at = _as_utc(now or datetime.now(UTC))
    if latest.state != "queued" or latest.attempt_number != 0:
        return False
    if checked_at - _as_utc(latest.recorded_at) < _QUEUED_RELAUNCH_AFTER:
        return False
    return launch_scenario_worker(generation_request.id, env=settings.env)


@router.post(
    "/api/issues/{issue_id}/scenario-sessions",
    response_model=ScenarioSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    issue_id: UUID,
    request: Request,
    response: Response,
    db: Session | None = Depends(_get_optional_db),
) -> ScenarioSessionCreateResponse:
    """Create one fixed-expiry session; never call or launch a provider."""
    _ensure_enabled()
    _set_private_headers(response)
    if not _rate_limiter.allow(_client_key(request), "session"):
        raise _public_error(status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited")
    if db is None:
        raise _public_error(status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable")
    try:
        if db.get(Market, issue_id) is None:
            raise _public_error(status.HTTP_404_NOT_FOUND, "issue_unavailable")
        created = create_scenario_session(db, issue_id)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise _public_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable"
        ) from exc
    if created is None:
        raise _public_error(status.HTTP_409_CONFLICT, "current_bundle_unavailable")
    session = created.session
    return ScenarioSessionCreateResponse(
        session_id=session.id,
        session_capability=created.capability,
        issue_id=session.market_id,
        created_at=_as_utc(session.created_at),
        expires_at=_as_utc(session.expires_at),
        max_turns=8,
        policy_version=session.policy_version,
        data_as_of=_as_utc(session.data_as_of),
        caution_note=session.caution_note,
    )


@router.get(
    "/api/issues/{issue_id}/scenario-sessions/{session_id}",
    response_model=ScenarioSessionResponse,
)
def get_session(
    issue_id: UUID,
    session_id: UUID,
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session | None = Depends(_get_optional_db),
) -> ScenarioSessionResponse:
    _ensure_enabled()
    _set_private_headers(response)
    if db is None:
        raise _public_error(status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable")
    session = _authenticate(db, issue_id, session_id, authorization)
    turns = list(
        db.execute(
            select(ScenarioTurn)
            .where(ScenarioTurn.session_id == session.id)
            .order_by(ScenarioTurn.sequence_number.asc())
        ).scalars()
    )
    premises = list(
        db.execute(
            select(ScenarioPremise)
            .where(ScenarioPremise.session_id == session.id)
            .order_by(ScenarioPremise.created_at.asc(), ScenarioPremise.id.asc())
        ).scalars()
    )
    user_turns = sum(turn.role == "user" for turn in turns)
    return ScenarioSessionResponse(
        session_id=session.id,
        issue_id=session.market_id,
        created_at=_as_utc(session.created_at),
        expires_at=_as_utc(session.expires_at),
        max_turns=8,
        remaining_turns=max(0, session.max_turns - user_turns),
        policy_version=session.policy_version,
        data_as_of=_as_utc(session.data_as_of),
        caution_note=session.caution_note,
        turns=[_turn_out(turn) for turn in turns],
        premises=[
            ScenarioPremiseOut(
                premise_id=premise.id,
                premise_class=premise.premise_class,
                text=premise.text,
                origin_turn_id=premise.origin_turn_id,
            )
            for premise in premises
        ],
    )


@router.post(
    "/api/issues/{issue_id}/scenario-sessions/{session_id}/turns",
    response_model=ScenarioTurnCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_turn(
    issue_id: UUID,
    session_id: UUID,
    body: ScenarioTurnCreateIn,
    request: Request,
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: UUID | None = Header(default=None, alias="Idempotency-Key"),
    db: Session | None = Depends(_get_optional_db),
) -> ScenarioTurnCreateResponse:
    """Append one user turn and queued request; never invoke a provider."""
    _ensure_enabled()
    _set_private_headers(response)
    if idempotency_key is None:
        raise _public_error(status.HTTP_400_BAD_REQUEST, "invalid_request")
    if not _rate_limiter.allow(_client_key(request), "turn"):
        raise _public_error(status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited")
    if db is None:
        raise _public_error(status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable")
    session = _authenticate(db, issue_id, session_id, authorization)
    try:
        result = enqueue_scenario_turn(
            db,
            session,
            body.message,
            str(idempotency_key),
        )
    except ScenarioUnavailableError as exc:
        raise _public_error(status.HTTP_404_NOT_FOUND, "session_unavailable") from exc
    except ScenarioStateError as exc:
        code_to_status = {
            "message_too_large": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "session_limit_reached": status.HTTP_409_CONFLICT,
            "turn_in_progress": status.HTTP_409_CONFLICT,
            "session_stale": status.HTTP_409_CONFLICT,
        }
        raise _public_error(code_to_status.get(exc.code, 400), exc.code) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise _public_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable"
        ) from exc
    if result.created:
        # The API commits first, then starts a request-scoped child. Provider
        # construction and all response validation remain outside this process.
        launch_scenario_worker(result.request.id, env=settings.env)
    return ScenarioTurnCreateResponse(
        turn_id=result.turn.id,
        sequence=result.turn.sequence_number,
        status="queued",
        created=result.created,
        requested_at=_as_utc(result.request.requested_at),
        stream_path=(
            f"/api/issues/{issue_id}/scenario-sessions/{session.id}/turns/"
            f"{result.turn.id}/stream"
        ),
    )


def _owned_request(
    db: Session,
    session_id: UUID,
    turn_id: UUID,
) -> tuple[ScenarioTurn, ScenarioGenerationRequest]:
    turn = db.get(ScenarioTurn, turn_id)
    if turn is None or turn.session_id != session_id or turn.role != "user":
        raise _public_error(status.HTTP_404_NOT_FOUND, "turn_unavailable")
    generation_request = db.execute(
        select(ScenarioGenerationRequest).where(
            ScenarioGenerationRequest.session_id == session_id,
            ScenarioGenerationRequest.user_turn_id == turn.id,
        )
    ).scalar_one_or_none()
    if generation_request is None:
        raise _public_error(status.HTTP_404_NOT_FOUND, "turn_unavailable")
    return turn, generation_request


@router.get(
    "/api/issues/{issue_id}/scenario-sessions/{session_id}/turns/{turn_id}",
    response_model=ScenarioTurnStatusResponse,
)
def get_turn(
    issue_id: UUID,
    session_id: UUID,
    turn_id: UUID,
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session | None = Depends(_get_optional_db),
) -> ScenarioTurnStatusResponse:
    _ensure_enabled()
    _set_private_headers(response)
    if db is None:
        raise _public_error(status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable")
    session = _authenticate(db, issue_id, session_id, authorization)
    turn, generation_request = _owned_request(db, session.id, turn_id)
    latest = latest_scenario_event(db, generation_request.id)
    if latest is None:
        raise _public_error(status.HTTP_409_CONFLICT, "request_state_unavailable")
    _maybe_relaunch_queued_request(generation_request, latest)
    return ScenarioTurnStatusResponse(
        turn_id=turn.id,
        sequence=turn.sequence_number,
        state=latest.state,
        attempt_number=latest.attempt_number,
        requested_at=_as_utc(generation_request.requested_at),
        updated_at=_as_utc(latest.recorded_at),
        assistant_turn_id=latest.assistant_turn_id,
        error_code=latest.error_code,
    )


def _sse_event(event: str, data: dict, *, event_id: int | None = None) -> str:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    lines.append("data: " + json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(lines) + "\n\n"


@router.get(
    "/api/issues/{issue_id}/scenario-sessions/{session_id}/turns/{turn_id}/stream"
)
def stream_turn(
    issue_id: UUID,
    session_id: UUID,
    turn_id: UUID,
    authorization: str | None = Header(default=None, alias="Authorization"),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    db: Session | None = Depends(_get_optional_db),
) -> StreamingResponse:
    """Replay only already-validated complete blocks for the owned turn."""
    _ensure_enabled()
    if db is None:
        raise _public_error(status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable")
    capability = _parse_capability(authorization)
    session = _authenticate(db, issue_id, session_id, authorization)
    _, generation_request = _owned_request(db, session.id, turn_id)
    try:
        after_block_id = max(0, int(last_event_id or "0"))
    except ValueError:
        after_block_id = 0

    def events() -> Generator[str, None, None]:
        nonlocal after_block_id
        last_status: tuple[str, int] | None = None
        last_heartbeat = time.monotonic()
        yield "retry: 1500\n\n"
        while True:
            db.rollback()
            try:
                authenticate_scenario_session(
                    db,
                    issue_id,
                    session_id,
                    capability,
                )
            except ScenarioUnavailableError:
                yield _sse_event("failed", {"error_code": "session_unavailable"})
                return
            latest = latest_scenario_event(db, generation_request.id)
            if latest is None:
                yield _sse_event("failed", {"error_code": "request_state_unavailable"})
                return
            _maybe_relaunch_queued_request(generation_request, latest)
            status_key = (latest.state, latest.attempt_number)
            if status_key != last_status:
                yield _sse_event(
                    "snapshot",
                    {
                        "state": latest.state,
                        "attempt_number": latest.attempt_number,
                        "updated_at": _as_utc(latest.recorded_at).isoformat(),
                    },
                )
                last_status = status_key
            if latest.state != "queued":
                blocks = db.execute(
                    select(ScenarioResponseBlock)
                    .where(
                        ScenarioResponseBlock.request_id == generation_request.id,
                        ScenarioResponseBlock.attempt_number == latest.attempt_number,
                        ScenarioResponseBlock.id > after_block_id,
                    )
                    .order_by(ScenarioResponseBlock.sequence_number.asc())
                ).scalars()
                for block in blocks:
                    after_block_id = block.id
                    yield _sse_event(
                        "block",
                        {
                            "sequence": block.sequence_number,
                            "block_type": block.block_type,
                            "payload": block.payload,
                        },
                        event_id=block.id,
                    )
            if latest.state == "succeeded":
                yield _sse_event(
                    "complete",
                    {"assistant_turn_id": str(latest.assistant_turn_id)},
                )
                return
            if latest.state == "failed":
                yield _sse_event("failed", {"error_code": latest.error_code})
                return
            if time.monotonic() - last_heartbeat >= 15:
                yield ": keep-alive\n\n"
                last_heartbeat = time.monotonic()
            time.sleep(0.25)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store, no-transform",
            "X-Accel-Buffering": "no",
            "Referrer-Policy": "no-referrer",
            "Vary": "Authorization, Origin",
        },
    )


@router.delete(
    "/api/issues/{issue_id}/scenario-sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    issue_id: UUID,
    session_id: UUID,
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session | None = Depends(_get_optional_db),
) -> None:
    """Delete only the authenticated ephemeral conversation graph."""
    _ensure_enabled()
    _set_private_headers(response)
    if db is None:
        raise _public_error(status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable")
    session = _authenticate(db, issue_id, session_id, authorization)
    try:
        delete_scenario_session(db, session)
    except SQLAlchemyError as exc:
        db.rollback()
        raise _public_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, "generation_unavailable"
        ) from exc
