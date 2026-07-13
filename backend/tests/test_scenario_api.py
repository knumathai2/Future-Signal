"""TASK-126 capability, API, replay, deletion, and limit tests."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.api.routes import scenarios
from app.core.config import Settings
from app.core.scenario_conversation import (
    cleanup_expired_scenario_sessions,
    create_scenario_session,
)
from app.db.models import (
    Market,
    ScenarioGenerationEvent,
    ScenarioGenerationRequest,
    ScenarioResponseBlock,
    ScenarioSession,
    ScenarioTurn,
)
from tests.conftest import MARKET_ID, seed_basic_market


@pytest.fixture(autouse=True)
def enabled_local_scenario(monkeypatch):
    monkeypatch.setattr(scenarios.settings, "scenario_conversation_enabled", True)
    monkeypatch.setattr(scenarios.settings, "env", "local")
    monkeypatch.setattr(scenarios, "launch_scenario_worker", lambda *_args, **_kwargs: True)
    scenarios._rate_limiter.reset()


def _create_session(live_client) -> dict:
    response = live_client.post(f"/api/issues/{MARKET_ID}/scenario-sessions", json={})
    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    return response.json()


def _auth(created: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {created['session_capability']}"}


def test_feature_is_default_off_and_non_local_guarded(live_client, db_session, monkeypatch):
    seed_basic_market(db_session)
    monkeypatch.setattr(scenarios.settings, "scenario_conversation_enabled", False)
    disabled = live_client.post(f"/api/issues/{MARKET_ID}/scenario-sessions", json={})
    assert disabled.status_code == 404
    assert disabled.json()["detail"]["code"] == "feature_unavailable"
    assert disabled.headers["cache-control"] == "no-store"
    assert disabled.headers["referrer-policy"] == "no-referrer"

    monkeypatch.setattr(scenarios.settings, "scenario_conversation_enabled", True)
    monkeypatch.setattr(scenarios.settings, "env", "production")
    production = live_client.post(f"/api/issues/{MARKET_ID}/scenario-sessions", json={})
    assert production.status_code == 404


def test_feature_flag_defaults_off_and_parses_explicit_true(monkeypatch):
    monkeypatch.delenv("SCENARIO_CONVERSATION_ENABLED", raising=False)
    assert Settings().scenario_conversation_enabled is False
    monkeypatch.setenv("SCENARIO_CONVERSATION_ENABLED", "true")
    assert Settings().scenario_conversation_enabled is True


def test_create_returns_capability_once_and_stores_only_hash(live_client, db_session):
    seed_basic_market(db_session)
    body = _create_session(live_client)

    assert body["issue_id"] == str(MARKET_ID)
    assert body["max_turns"] == 8
    assert body["policy_version"] == "summary-scenario-policy-1"
    assert "session_capability" in body
    stored = db_session.get(ScenarioSession, uuid.UUID(body["session_id"]))
    assert stored is not None
    assert stored.capability_hash != body["session_capability"]
    assert len(stored.capability_hash) == 64

    read = live_client.get(
        f"/api/issues/{MARKET_ID}/scenario-sessions/{body['session_id']}",
        headers=_auth(body),
    )
    assert read.status_code == 200
    assert "session_capability" not in read.json()
    assert read.json()["remaining_turns"] == 8


def test_capability_is_required_and_cross_session_access_is_hidden(live_client, db_session):
    seed_basic_market(db_session)
    first = _create_session(live_client)
    second = _create_session(live_client)
    path = f"/api/issues/{MARKET_ID}/scenario-sessions/{second['session_id']}"

    missing = live_client.get(path)
    assert missing.status_code == 401
    assert missing.json()["detail"]["code"] == "session_token_required"
    malformed = live_client.get(path, headers={"Authorization": "Bearer too-short"})
    assert malformed.status_code == 401
    cross_session = live_client.get(path, headers=_auth(first))
    assert cross_session.status_code == 404
    assert cross_session.json()["detail"]["code"] == "session_unavailable"


def test_turn_is_idempotent_and_one_in_flight(live_client, db_session):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    path = f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns"
    idempotency = str(uuid.uuid4())
    headers = {**_auth(created), "Idempotency-Key": idempotency}

    first = live_client.post(path, headers=headers, json={"message": "조건을 비교해 주세요."})
    assert first.status_code == 202
    assert first.json()["created"] is True
    repeated = live_client.post(path, headers=headers, json={"message": "ignored duplicate"})
    assert repeated.status_code == 202
    assert repeated.json()["created"] is False
    assert repeated.json()["turn_id"] == first.json()["turn_id"]

    second = live_client.post(
        path,
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "다른 조건도 확인해 주세요."},
    )
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "turn_in_progress"
    assert db_session.query(ScenarioTurn).count() == 1
    assert db_session.query(ScenarioGenerationRequest).count() == 1
    assert db_session.query(ScenarioGenerationEvent).count() == 1


def test_new_turn_launches_worker_once_after_commit(live_client, db_session, monkeypatch):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    calls = []
    monkeypatch.setattr(
        scenarios,
        "launch_scenario_worker",
        lambda request_id, *, env, **_kwargs: calls.append((request_id, env)) or True,
    )
    path = f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns"
    idempotency = str(uuid.uuid4())
    headers = {**_auth(created), "Idempotency-Key": idempotency}

    first = live_client.post(path, headers=headers, json={"message": "조건을 살펴봐 주세요."})
    repeated = live_client.post(path, headers=headers, json={"message": "같은 요청"})

    assert first.status_code == 202
    assert repeated.status_code == 202
    assert repeated.json()["created"] is False
    assert len(calls) == 1
    assert calls[0][1] == "local"
    request = db_session.query(ScenarioGenerationRequest).one()
    assert calls[0][0] == request.id


def test_stale_attempt_zero_request_is_relaunched_with_bounded_helper(
    live_client,
    db_session,
    monkeypatch,
):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    response = live_client.post(
        f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns",
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "조건을 살펴봐 주세요."},
    )
    assert response.status_code == 202
    request = db_session.query(ScenarioGenerationRequest).one()
    event = db_session.query(ScenarioGenerationEvent).one()
    calls = []
    monkeypatch.setattr(
        scenarios,
        "launch_scenario_worker",
        lambda request_id, *, env, **_kwargs: calls.append((request_id, env)) or True,
    )

    assert (
        scenarios._maybe_relaunch_queued_request(
            request,
            event,
            now=event.recorded_at + timedelta(seconds=4),
        )
        is False
    )
    assert scenarios._maybe_relaunch_queued_request(
        request,
        event,
        now=event.recorded_at + timedelta(seconds=6),
    )
    assert calls == [(request.id, "local")]


def test_message_limit_returns_413_before_append(live_client, db_session):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    response = live_client.post(
        f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns",
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "가" * 1001},
    )
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "message_too_large"
    assert db_session.query(ScenarioTurn).count() == 0


def test_changed_input_fingerprint_requires_a_new_session(live_client, db_session):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    session = db_session.get(ScenarioSession, uuid.UUID(created["session_id"]))
    assert session is not None
    session.input_fingerprint = "0" * 64
    db_session.commit()

    response = live_client.post(
        f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns",
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "현재 조건을 살펴봐 주세요."},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "session_stale"
    assert db_session.query(ScenarioTurn).count() == 0


def test_eight_turn_limit_fails_before_ninth_append(live_client, db_session):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    path = f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns"
    for index in range(8):
        response = live_client.post(
            path,
            headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
            json={"message": f"조건 {index + 1}을 살펴봐 주세요."},
        )
        assert response.status_code == 202
        request = (
            db_session.query(ScenarioGenerationRequest)
            .filter_by(user_turn_id=uuid.UUID(response.json()["turn_id"]))
            .one()
        )
        db_session.add(
            ScenarioGenerationEvent(
                request_id=request.id,
                session_id=request.session_id,
                state="failed",
                attempt_number=1,
                recorded_at=datetime.now(UTC) + timedelta(seconds=index),
                lease_token=None,
                lease_expires_at=None,
                assistant_turn_id=None,
                error_code="generation_unavailable",
                usage={},
            )
        )
        db_session.commit()

    ninth = live_client.post(
        path,
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "아홉 번째 조건을 살펴봐 주세요."},
    )
    assert ninth.status_code == 409
    assert ninth.json()["detail"]["code"] == "session_limit_reached"
    assert db_session.query(ScenarioTurn).filter_by(role="user").count() == 8


def test_turn_status_and_authenticated_stream_replay_validated_blocks(
    live_client,
    db_session,
    monkeypatch,
):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    turn_path = f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns"
    queued = live_client.post(
        turn_path,
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "조건부 경로를 설명해 주세요."},
    ).json()
    user_turn_id = uuid.UUID(queued["turn_id"])
    request = db_session.query(ScenarioGenerationRequest).filter_by(user_turn_id=user_turn_id).one()
    assistant_turn = ScenarioTurn(
        id=uuid.uuid4(),
        session_id=request.session_id,
        sequence_number=2,
        role="assistant",
        content="조건부 경로에서는 공식 정보의 일치 여부를 먼저 확인합니다.",
        idempotency_key_hash=None,
        created_at=datetime.now(UTC),
    )
    db_session.add(assistant_turn)
    db_session.add(
        ScenarioGenerationEvent(
            request_id=request.id,
            session_id=request.session_id,
            state="running",
            attempt_number=1,
            recorded_at=datetime.now(UTC),
            lease_token=uuid.uuid4(),
            lease_expires_at=datetime.now(UTC) + timedelta(minutes=5),
            assistant_turn_id=None,
            error_code=None,
            usage={},
        )
    )
    db_session.flush()
    db_session.add_all(
        [
            ScenarioResponseBlock(
                id=1,
                request_id=request.id,
                attempt_number=1,
                sequence_number=0,
                block_type="paragraph",
                payload={"text": assistant_turn.content},
                recorded_at=datetime.now(UTC),
            ),
            ScenarioResponseBlock(
                id=2,
                request_id=request.id,
                attempt_number=1,
                sequence_number=1,
                block_type="list",
                payload={"ordered": False, "items": ["공식 자료를 다시 확인합니다."]},
                recorded_at=datetime.now(UTC),
            ),
            ScenarioResponseBlock(
                id=3,
                request_id=request.id,
                attempt_number=1,
                sequence_number=2,
                block_type="paragraph",
                payload={"text": "공개 정보에는 시간 차이가 있을 수 있습니다."},
                recorded_at=datetime.now(UTC),
            ),
        ]
    )
    db_session.add(
        ScenarioGenerationEvent(
            request_id=request.id,
            session_id=request.session_id,
            state="succeeded",
            attempt_number=1,
            recorded_at=datetime.now(UTC) + timedelta(seconds=1),
            lease_token=None,
            lease_expires_at=None,
            assistant_turn_id=assistant_turn.id,
            error_code=None,
            usage={"total_tokens": 100},
        )
    )
    db_session.commit()

    status_response = live_client.get(
        f"{turn_path}/{user_turn_id}",
        headers=_auth(created),
    )
    assert status_response.status_code == 200
    assert status_response.json()["state"] == "succeeded"
    sleep_calls = []
    monkeypatch.setattr(scenarios.time, "sleep", sleep_calls.append)
    stream = live_client.get(
        f"{turn_path}/{user_turn_id}/stream",
        headers=_auth(created),
    )
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert stream.text.count("event: block") == 3
    assert '"block_type":"paragraph"' in stream.text
    assert stream.text.index('"sequence":0') < stream.text.index('"sequence":1')
    assert stream.text.index('"sequence":1') < stream.text.index('"sequence":2')
    assert "event: complete" in stream.text
    assert created["session_capability"] not in stream.text
    assert sleep_calls == [scenarios._VALIDATED_BLOCK_REPLAY_DELAY_SECONDS] * 2


def test_owner_delete_removes_only_ephemeral_graph(live_client, db_session):
    seed_basic_market(db_session)
    created = _create_session(live_client)
    turn_path = f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}/turns"
    live_client.post(
        turn_path,
        headers={**_auth(created), "Idempotency-Key": str(uuid.uuid4())},
        json={"message": "하나의 조건을 살펴봐 주세요."},
    )
    deleted = live_client.delete(
        f"/api/issues/{MARKET_ID}/scenario-sessions/{created['session_id']}",
        headers=_auth(created),
    )
    assert deleted.status_code == 204
    assert db_session.get(ScenarioSession, uuid.UUID(created["session_id"])) is None
    assert db_session.get(Market, MARKET_ID) is not None
    assert db_session.query(ScenarioTurn).count() == 0
    assert db_session.query(ScenarioGenerationRequest).count() == 0


def test_expiry_cleanup_deletes_only_expired_session(db_session):
    seed_basic_market(db_session)
    now = datetime.now(UTC)
    expired = create_scenario_session(
        db_session,
        MARKET_ID,
        now=now - timedelta(hours=25),
        capability="expired-capability",
    )
    live = create_scenario_session(
        db_session,
        MARKET_ID,
        now=now,
        capability="live-capability",
    )
    assert expired is not None and live is not None

    assert cleanup_expired_scenario_sessions(db_session, now=now) == 1
    assert db_session.get(ScenarioSession, expired.session.id) is None
    assert db_session.get(ScenarioSession, live.session.id) is not None


def test_local_rate_limits_session_creation(live_client, db_session):
    seed_basic_market(db_session)
    for _ in range(3):
        assert _create_session(live_client)["session_id"]
    limited = live_client.post(f"/api/issues/{MARKET_ID}/scenario-sessions", json={})
    assert limited.status_code == 429
    assert limited.json()["detail"]["code"] == "rate_limited"


def test_openapi_contains_approved_scenario_paths(live_client):
    document = live_client.get("/openapi.json").json()
    assert document["info"]["version"] == "0.4.0"
    paths = document["paths"]
    assert "/api/issues/{issue_id}/scenario-sessions" in paths
    assert "/api/issues/{issue_id}/scenario-sessions/{session_id}" in paths
    assert "/api/issues/{issue_id}/scenario-sessions/{session_id}/turns" in paths
    assert "/api/issues/{issue_id}/scenario-sessions/{session_id}/turns/{turn_id}/stream" in paths
