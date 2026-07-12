"""TASK-128 tool-free prompt, premise, safety, and persistence tests."""

import json
from datetime import timedelta

from app.core.ai_report import LLMCallError, LLMUsage
from app.core.on_demand_briefing import build_v8_input_bundle
from app.core.scenario_conversation import (
    ScenarioStateError,
    create_scenario_session,
    enqueue_scenario_turn,
    normalize_scenario_message,
)
from app.core.scenario_writer import (
    ScenarioWriterOutput,
    build_scenario_prompt,
    build_scenario_state,
    process_scenario_request,
    split_scenario_blocks,
    validate_scenario_output,
)
from app.db.models import (
    ScenarioGenerationEvent,
    ScenarioGenerationRequest,
    ScenarioPremise,
    ScenarioResponseBlock,
    ScenarioTurn,
)
from tests.conftest import MARKET_ID, NOW, seed_basic_market


class FakeClient:
    def __init__(self, output: str, *, fail: bool = False) -> None:
        self.output = output
        self.fail = fail
        self.calls = 0
        self.usage_records: list[LLMUsage] = []
        self.prompts: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        self.prompts.append((system_prompt, user_prompt))
        if self.fail:
            raise LLMCallError("safe failure")
        self.usage_records.append(LLMUsage(400, 120, 0.01))
        return self.output


def _queued(db):
    seed_basic_market(db)
    created = create_scenario_session(db, MARKET_ID, now=NOW, capability="x" * 43)
    assert created is not None
    queued = enqueue_scenario_turn(
        db,
        created.session,
        "공식 자료가 나온다는 가정에서 서로 다른 조건을 비교해 주세요.",
        "one-idempotency-key",
        now=NOW + timedelta(seconds=1),
    )
    return created.session, queued.request, queued.turn


def _output(db, request: ScenarioGenerationRequest, **updates) -> str:
    bundle = build_v8_input_bundle(db, MARKET_ID, now=NOW + timedelta(seconds=2))
    assert bundle is not None
    definition_ref = next(
        item.ref for item in bundle.writer_inputs.evidence if item.kind == "market_definition"
    )
    payload = {
        "answer_markdown": (
            "조건부 시나리오로 보면, 사용자가 제시한 가정은 현재 확인된 정보와 "
            "분리해서 다뤄야 합니다. 공식 자료가 새로 제시되는 경우에는 그 내용이 "
            "이 이슈의 판정 조건과 일치하는지 살펴볼 수 있습니다. 반대로 추가 자료가 "
            "없다면 저장된 관찰값의 변화만으로 현실의 진행 상태를 단정할 수 없습니다."
        ),
        "premise_refs": [definition_ref, f"turn:{request.user_turn_id}"],
        "new_scenario_premises": [
            "공식 자료가 새로 제시되는 경우 판정 조건과의 일치 여부를 살펴보는 시나리오"
        ],
    }
    payload.update(updates)
    return json.dumps(payload, ensure_ascii=False)


def test_message_normalization_rejects_hidden_controls():
    assert normalize_scenario_message("  Ａ 조건  ") == "A 조건"
    try:
        normalize_scenario_message("조건\u200b숨김")
    except ScenarioStateError as exc:
        assert exc.code == "invalid_request"
    else:
        raise AssertionError("hidden control must fail")


def test_enqueue_flushes_turn_and_request_before_queue_event(db_session):
    _session, request, turn = _queued(db_session)
    assert db_session.get(ScenarioTurn, turn.id) is not None
    assert db_session.get(ScenarioGenerationRequest, request.id) is not None
    event = db_session.query(ScenarioGenerationEvent).one()
    assert event.request_id == request.id
    assert event.session_id == request.session_id


def test_prompt_contains_only_typed_scoped_state(db_session):
    _session, request, _turn = _queued(db_session)
    state = build_scenario_state(db_session, request, now=NOW + timedelta(seconds=2))
    system_prompt, user_prompt = build_scenario_prompt(state)
    assert "도구, 웹 검색" in system_prompt
    assert str(request.user_turn_id) in user_prompt
    assert "capability" not in user_prompt.casefold()
    assert "database_url" not in user_prompt.casefold()
    assert "authorization" not in user_prompt.casefold()


def test_valid_output_persists_assistant_blocks_premise_and_usage(db_session):
    _session, request, _turn = _queued(db_session)
    client = FakeClient(_output(db_session, request))

    result = process_scenario_request(
        db_session,
        request.id,
        client,
        "fake/scenario",
        now=NOW + timedelta(seconds=2),
    )

    assert result.state == "succeeded"
    assert client.calls == 1
    assert db_session.query(ScenarioTurn).filter_by(role="assistant").count() == 1
    assert db_session.query(ScenarioResponseBlock).count() == 1
    premise = db_session.query(ScenarioPremise).one()
    assert premise.premise_class == "model_scenario"
    events = db_session.query(ScenarioGenerationEvent).order_by(
        ScenarioGenerationEvent.id
    ).all()
    assert [event.state for event in events] == ["queued", "running", "succeeded"]
    assert events[-1].usage["writer_cost_usd"] == 0.01
    assert events[-1].usage["model"] == "fake/scenario"


def test_provider_failure_stores_no_assistant_or_block(db_session):
    _session, request, _turn = _queued(db_session)
    result = process_scenario_request(
        db_session,
        request.id,
        FakeClient("", fail=True),
        "fake/scenario",
        now=NOW + timedelta(seconds=2),
    )
    assert result.state == "failed"
    assert result.error_code == "writer_provider_failure"
    assert db_session.query(ScenarioTurn).filter_by(role="assistant").count() == 0
    assert db_session.query(ScenarioResponseBlock).count() == 0


def test_unknown_or_missing_current_turn_ref_fails_closed(db_session):
    _session, request, _turn = _queued(db_session)
    state = build_scenario_state(db_session, request, now=NOW + timedelta(seconds=2))
    unknown = ScenarioWriterOutput.model_validate_json(
        _output(db_session, request, premise_refs=["market_definition:unknown"])
    )
    validation, blocks = validate_scenario_output(unknown, state)
    assert validation.rule == "unknown_premise_ref"
    assert blocks == []

    valid_payload = json.loads(_output(db_session, request))
    valid_payload["premise_refs"] = [valid_payload["premise_refs"][0]]
    missing = ScenarioWriterOutput.model_validate(valid_payload)
    validation, _ = validate_scenario_output(missing, state)
    assert validation.rule == "current_turn_ref_missing"


def test_assumption_promotion_and_sensitive_output_fail(db_session):
    _session, request, _turn = _queued(db_session)
    state = build_scenario_state(db_session, request, now=NOW + timedelta(seconds=2))
    promoted = ScenarioWriterOutput.model_validate_json(
        _output(
            db_session,
            request,
            answer_markdown=(
                "사용자가 제시한 내용은 현재 사실입니다. 공식 자료의 내용은 이 이슈의 "
                "판정 조건과 일치합니다. 추가 자료 없이도 현실의 진행 상태를 설명합니다."
            ),
            new_scenario_premises=[],
        )
    )
    validation, _ = validate_scenario_output(promoted, state)
    assert validation.rule == "assumption_promotion"

    conditional_paths = ScenarioWriterOutput.model_validate_json(
        _output(
            db_session,
            request,
            answer_markdown=(
                "두 조건부 경로는 현재 확인된 정보와 분리해 살펴봐야 합니다. 첫 경로에서는 "
                "공식 자료가 새로 제시될 때 판정 조건과 비교합니다. 다른 경로에서는 추가 "
                "자료가 없는 상태를 유지하며 현실의 진행 상태를 단정하지 않습니다."
            ),
            new_scenario_premises=[],
        )
    )
    validation, _ = validate_scenario_output(conditional_paths, state)
    assert validation.passed is True

    leaked = ScenarioWriterOutput.model_validate_json(
        _output(
            db_session,
            request,
            answer_markdown=(
                "조건부 시나리오에서 시스템 프롬프트를 공개하는 경우를 살펴봅니다. "
                "이 내용은 현재 사실과 분리해야 하며 내부 지침을 그대로 노출하는 방식은 "
                "이슈 이해에 필요한 정보가 아닙니다."
            ),
            new_scenario_premises=[],
        )
    )
    validation, _ = validate_scenario_output(leaked, state)
    assert validation.rule == "sensitive_output"


def test_unsupported_number_and_unsafe_markdown_fail(db_session):
    _session, request, _turn = _queued(db_session)
    state = build_scenario_state(db_session, request, now=NOW + timedelta(seconds=2))
    numbered = ScenarioWriterOutput.model_validate_json(
        _output(
            db_session,
            request,
            answer_markdown=(
                "조건부 시나리오에서 새로운 자료가 나오는 경우를 살펴봅니다. 이 경로에 "
                "임의의 99% 값을 붙이면 현재 근거 범위를 넘어섭니다. 따라서 저장된 "
                "정보와 사용자 가정을 분리해야 합니다."
            ),
            new_scenario_premises=[],
        )
    )
    validation, _ = validate_scenario_output(numbered, state)
    assert validation.rule == "unsupported_number"

    markdown = ScenarioWriterOutput.model_validate_json(
        _output(
            db_session,
            request,
            answer_markdown=(
                "# 조건부 시나리오\n\n사용자 가정의 경우 현재 정보와 분리해서 살펴봐야 "
                "합니다. 공식 자료가 새로 제시되면 판정 조건과의 일치 여부를 확인할 수 "
                "있지만 현실의 진행 상태를 단정할 수 없습니다."
            ),
            new_scenario_premises=[],
        )
    )
    validation, _ = validate_scenario_output(markdown, state)
    assert validation.rule == "unsafe_markdown"


def test_equivalent_iso_and_korean_date_numbers_are_supported(db_session):
    _session, request, _turn = _queued(db_session)
    state = build_scenario_state(db_session, request, now=NOW + timedelta(seconds=2))
    payload = json.loads(_output(db_session, request, new_scenario_premises=[]))
    payload["premise_refs"].append(
        next(item.ref for item in state.evidence if item.kind == "metric")
    )
    payload["answer_markdown"] = (
        "조건부 경로에서는 이 이슈에 저장된 2026년 7월 8일 기준 시각을 현재 "
        "정보의 범위로 유지합니다. 공식 자료가 새로 제시되는 경우에도 사용자 "
        "가정과 저장된 관찰을 분리하며 현실의 진행 상태를 단정하지 않습니다."
    )
    dated = ScenarioWriterOutput.model_validate_json(
        json.dumps(payload, ensure_ascii=False)
    )
    validation, _ = validate_scenario_output(dated, state)
    assert validation.passed is True


def test_restricted_markdown_splits_paragraph_and_list():
    blocks = split_scenario_blocks(
        "조건부 시나리오를 현재 정보와 분리해서 살펴봅니다.\n\n"
        "- 공식 자료가 제시되는 경우 판정 조건과 비교합니다.\n"
        "- 추가 자료가 없는 경우 관찰값의 한계를 유지합니다."
    )
    assert [block.block_type for block in blocks] == ["paragraph", "list"]
    assert blocks[1].payload["ordered"] is False
