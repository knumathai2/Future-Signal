"""TASK-105 v7 generate/status/cache/report public API tests."""

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.core.on_demand_briefing import build_v8_input_bundle, process_v8_request
from app.db.models import (
    AiReport,
    AiReportGenerationRequest,
    ContextCandidate,
    MarketMetric,
    MarketSnapshot,
)
from tests.conftest import MARKET_ID, NOW, seed_basic_market


@pytest.fixture(autouse=True)
def worker_launches(monkeypatch):
    launches = []

    def record_launch(request_id, *, env):
        launches.append((request_id, env))
        return True

    monkeypatch.setattr(
        "app.api.routes.issues.launch_on_demand_worker",
        record_launch,
    )
    return launches


class FakeLLM:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def complete(self, _system, _user):
        self.calls += 1
        return self.response


def _output(*, metric_id: int = 1) -> str:
    return json.dumps(
        {
            "headline": "공식 조건과 현재 공개 자료를 함께 정리한 브리핑",
            "summary": (
                "이 이슈는 저장된 설명에 따라 공식 조건이 충족되는지를 확인합니다. "
                "현재 자료에는 기준 시각의 관찰값과 최근 비교값이 포함되어 있습니다. "
                "최근 흐름은 이전보다 달라졌지만 실제 결과를 뜻하지 않으며, 제공된 "
                "근거 범위에서 현재 상황과 앞으로 확인할 조건을 함께 정리합니다."
            ),
            "sections": [
                {
                    "type": "current_situation",
                    "title": "이슈의 기준",
                    "format": "paragraph",
                    "content": (
                        "저장된 이슈 설명에 따라 공식 조건이 충족되는지를 확인하는 대상입니다."
                    ),
                    "items": [],
                    "evidence_refs": [f"market_definition:market-{MARKET_ID}"],
                },
                {
                    "type": "recent_change",
                    "title": "저장된 공개 데이터",
                    "format": "paragraph",
                    "content": (
                        "기준 시각의 관찰값과 최근 비교값을 서로 구분하여 살펴볼 수 있습니다."
                    ),
                    "items": [],
                    "evidence_refs": [f"metric:{metric_id}"],
                },
            ],
        },
        ensure_ascii=False,
    )


def _enqueue(live_client, *, refresh_context=False):
    response = live_client.post(
        f"/api/issues/{MARKET_ID}/report/generate",
        json={"refresh_context": refresh_context},
    )
    assert response.status_code == 202
    return response.json()


def _process(db_session, request_id: str, *, output=None):
    client = FakeLLM(output or _output())
    request = db_session.get(AiReportGenerationRequest, UUID(request_id))
    result = process_v8_request(
        db_session,
        UUID(request_id),
        client,
        "fake/writer",
        now=request.requested_at,
    )
    return result, client


def _add_metric(db_session, *, metric_id: int, at: datetime, price: float):
    db_session.add(
        MarketSnapshot(
            id=metric_id,
            market_id=MARKET_ID,
            captured_at=at,
            price=price,
            volume_24h=1000,
            volume_total=50000,
            liquidity=2000,
            best_bid=None,
            best_ask=None,
        )
    )
    db_session.add(
        MarketMetric(
            id=metric_id,
            market_id=MARKET_ID,
            computed_at=at,
            change_24h=0.01,
            change_7d=0.02,
            volatility_score=0.1,
            attention_score=0.2,
            heat_score=10,
            confidence_level="sufficient",
        )
    )
    db_session.commit()


def _add_context(db_session):
    candidate_id = UUID("88888888-8888-4888-8888-888888888888")
    db_session.add(
        ContextCandidate(
            id=candidate_id,
            market_id=MARKET_ID,
            episode_at=NOW,
            event_title="기관 공식 문서 공개",
            event_at=NOW,
            neutral_summary="기관이 조건과 관련된 공식 문서를 공개했습니다.",
            sources=[
                {
                    "citation_id": "citation:api-source",
                    "title": "기관 공식 문서",
                    "url": "https://example.gov/document",
                    "canonical_url": "https://example.gov/document",
                    "domain": "example.gov",
                    "level": "A",
                    "accepted": True,
                    "reason_code": "accepted_level_a",
                    "supported_claims": [
                        {
                            "ref": "claim:api-source",
                            "text": "기관이 공식 문서를 공개했습니다.",
                            "excerpt": "기관 공식 문서가 공개되었습니다.",
                            "citation_id": "citation:api-source",
                        }
                    ],
                    "content_hash": "api-source-hash",
                }
            ],
            verification_state="verified",
            verification_score_internal=1,
            research_model="openai/research",
            verifier_model="deterministic",
            policy_version="v7-source-level-1",
            evidence_hash="api-context-hash",
            collected_at=NOW,
            expires_at=NOW + timedelta(days=30),
        )
    )
    db_session.commit()
    return candidate_id


def test_report_starts_idle_without_v7_request(live_client, db_session):
    seed_basic_market(db_session)
    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_generate_joins_duplicate_and_status_endpoint_reports_queue(
    live_client, db_session, worker_launches
):
    seed_basic_market(db_session)
    first = _enqueue(live_client)
    second = _enqueue(live_client)
    assert first["created"] is True
    assert second["created"] is False
    assert first["request_id"] == second["request_id"]
    assert worker_launches == [
        (UUID(first["request_id"]), "local"),
        (UUID(first["request_id"]), "local"),
    ]

    report = live_client.get(f"/api/issues/{MARKET_ID}/report").json()
    assert report["status"] == "generating"
    assert report["request_id"] == first["request_id"]

    status_response = live_client.get(
        f"/api/issues/{MARKET_ID}/report/requests/{first['request_id']}"
    )
    assert status_response.status_code == 200
    assert status_response.json()["state"] == "queued"
    assert status_response.json()["attempt_number"] == 0


def test_generate_keeps_committed_queue_when_worker_spawn_fails(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)
    monkeypatch.setattr(
        "app.api.routes.issues.launch_on_demand_worker",
        lambda *_args, **_kwargs: False,
    )

    request = _enqueue(live_client)

    status_response = live_client.get(
        f"/api/issues/{MARKET_ID}/report/requests/{request['request_id']}"
    )
    assert status_response.status_code == 200
    assert status_response.json()["state"] == "queued"


def test_worker_result_is_served_as_fresh_v8(live_client, db_session):
    seed_basic_market(db_session)
    request = _enqueue(live_client)
    result, client = _process(db_session, request["request_id"])
    assert result.state == "succeeded"
    assert client.calls == 1

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "fresh"
    assert body["report_version"] == "v8"
    assert body["headline"].startswith("공식 조건")
    assert [section["type"] for section in body["sections"]] == [
        "current_situation",
        "recent_change",
    ]
    assert body["sources"] == []
    assert body["cache"]["state"] == "fresh"
    assert body["data_as_of"].startswith("2026-07-08T09:00:00")
    assert body["caution_note"]


def test_v7_api_exposes_exact_level_claim_and_safe_source(live_client, db_session):
    seed_basic_market(db_session)
    candidate_id = _add_context(db_session)
    request = _enqueue(live_client)
    bundle = build_v8_input_bundle(db_session, MARKET_ID, now=datetime.now(UTC))
    assert bundle is not None
    source_item = next(item for item in bundle.writer_inputs.evidence if item.kind == "source")
    raw = json.loads(_output())
    raw["sections"].append(
        {
            "type": "interpretation",
            "title": "확인된 공식 자료",
            "format": "paragraph",
            "content": "기관이 공개한 공식 문서의 지원 문장을 출처와 함께 확인할 수 있습니다.",
            "items": [],
            "evidence_refs": [f"context:{candidate_id}", source_item.ref],
        }
    )
    result, _ = _process(
        db_session,
        request["request_id"],
        output=json.dumps(raw, ensure_ascii=False),
    )
    assert result.state == "succeeded"

    body = live_client.get(f"/api/issues/{MARKET_ID}/report").json()
    assert body["status"] == "fresh"
    assert body["sources"] == [
        {
            "id": source_item.ref,
            "context_ref": f"context:{candidate_id}",
            "citation_id": "citation:api-source",
            "title": "기관 공식 문서",
            "url": "https://example.gov/document",
            "domain": "example.gov",
            "source_level": "A",
            "supported_claims": [
                {
                    "ref": "claim:api-source",
                    "text": "기관이 공식 문서를 공개했습니다.",
                    "excerpt": "기관 공식 문서가 공개되었습니다.",
                    "citation_id": "citation:api-source",
                }
            ],
            "retrieved_at": "2026-07-08T09:00:00Z",
        }
    ]


def test_new_metric_marks_last_good_report_stale(live_client, db_session):
    seed_basic_market(db_session)
    request = _enqueue(live_client)
    _process(db_session, request["request_id"])
    _add_metric(db_session, metric_id=2, at=NOW + timedelta(hours=1), price=0.64)

    body = live_client.get(f"/api/issues/{MARKET_ID}/report").json()
    assert body["status"] == "stale"
    assert body["cache"]["state"] == "stale"
    assert body["cache"]["current_fingerprint"] != body["cache"]["input_fingerprint"]


def test_refresh_with_additional_writer_number_replaces_last_good(live_client, db_session):
    seed_basic_market(db_session)
    first = _enqueue(live_client)
    _process(db_session, first["request_id"])
    _add_metric(db_session, metric_id=2, at=NOW + timedelta(hours=1), price=0.64)
    second = _enqueue(live_client)
    invalid = json.loads(_output(metric_id=2))
    invalid["sections"][1]["content"] += " 근거에 없는 99를 추가했습니다."
    result, _ = _process(
        db_session,
        second["request_id"],
        output=json.dumps(invalid, ensure_ascii=False),
    )
    assert result.state == "succeeded"

    body = live_client.get(f"/api/issues/{MARKET_ID}/report").json()
    assert body["status"] == "fresh"
    assert body["id"] == str(result.report_id)
    assert db_session.query(AiReport).count() == 2


def test_malformed_latest_v7_falls_back_to_previous_valid_row(live_client, db_session):
    seed_basic_market(db_session)
    first = _enqueue(live_client)
    _process(db_session, first["request_id"])
    good_report = db_session.query(AiReport).one()

    bad_report = AiReport(
        id=UUID("99999999-9999-4999-8999-999999999999"),
        market_id=MARKET_ID,
        generated_at=datetime.now(UTC) + timedelta(minutes=1),
        input_metrics_id=1,
        content={"report_version": "v8", "unexpected": True},
        model_used="fake/writer",
        prompt_version="v8",
        status="success",
    )
    db_session.add(bad_report)
    db_session.commit()

    body = live_client.get(f"/api/issues/{MARKET_ID}/report").json()
    assert body["id"] == str(good_report.id)
    assert body["status"] == "fresh"


def test_generation_request_is_scoped_to_issue(live_client, db_session):
    seed_basic_market(db_session)
    request = _enqueue(live_client)
    response = live_client.get(
        f"/api/issues/does-not-exist/report/requests/{request['request_id']}"
    )
    assert response.status_code == 404


def test_generate_rejects_unknown_issue_and_extra_body_fields(live_client, db_session):
    seed_basic_market(db_session)
    unknown = live_client.post(
        "/api/issues/does-not-exist/report/generate",
        json={"refresh_context": False},
    )
    assert unknown.status_code == 404
    invalid = live_client.post(
        f"/api/issues/{MARKET_ID}/report/generate",
        json={"refresh_context": False, "unexpected": True},
    )
    assert invalid.status_code == 422
