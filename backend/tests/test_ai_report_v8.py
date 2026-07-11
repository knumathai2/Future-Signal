"""TASK-112 v8 issue-centered writer contract tests."""

import json
import uuid

import pytest

from app.core.ai_report import (
    V7EvidenceItem,
    V8StreamCompleteBlock,
    V8StreamHeadlineBlock,
    V8StreamSectionBlock,
    V8WriterInputs,
    build_v8_prompt,
    build_v8_stream_prompt,
    parse_v8_stream_line,
    parse_v8_writer_output,
    validate_v8_stream_block,
    validate_v8_writer_output,
)

ISSUE_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")


def _inputs() -> V8WriterInputs:
    return V8WriterInputs(
        issue_id=ISSUE_ID,
        title="정부 기관의 공식 결정 조건",
        category="정치",
        evidence=[
            V7EvidenceItem(
                ref="market_definition:rule-1",
                kind="market_definition",
                text="공식 문서에 결정이 기록되는지를 확인하는 이슈입니다.",
            ),
            V7EvidenceItem(
                ref="metric:42",
                kind="metric",
                text=(
                    '{"current_value_percent":12.0,"change_7d_pp":-3.0,'
                    '"comparison_window_7d_days":7}'
                ),
            ),
            V7EvidenceItem(
                ref="context:ctx-1",
                kind="context",
                text="기관이 관련 절차 일정을 공개했습니다.",
            ),
            V7EvidenceItem(
                ref="source:src-1",
                kind="source",
                text=(
                    '{"title":"기관 공식 일정 문서","supported_claims":['
                    '{"text":"The parliament opening was confirmed and the committee '
                    "recommended the schedule as an opportunity. The document guarantees "
                    'speaking access, gives a forecast, and states the cause."}]}'
                ),
                parent_ref="context:ctx-1",
                source_level="A",
            ),
        ],
    )


def _raw_output() -> dict:
    return {
        "headline": "공식 결정 전 확인해야 할 현재 상황",
        "summary": (
            "이 이슈는 기관의 공식 문서에 결정이 기록되는지를 확인합니다. 현재 제공된 "
            "공개 자료에는 관련 절차 일정이 담겨 있지만 최종 결정은 확인되지 않았습니다. "
            "최근 관찰값은 일주일 전보다 낮아졌으며, 이 변화는 실제 결과가 아니라 저장된 "
            "공개 데이터에 나타난 기대 흐름으로만 읽어야 합니다."
        ),
        "sections": [
            {
                "type": "current_situation",
                "title": "현재 확인된 상황",
                "format": "paragraph",
                "content": (
                    "공식 문서에 결정이 기록되는지가 핵심이며, 현재 자료에서는 관련 절차 "
                    "일정까지만 확인됩니다."
                ),
                "items": [],
                "evidence_refs": [
                    "market_definition:rule-1",
                    "context:ctx-1",
                    "source:src-1",
                ],
            },
            {
                "type": "recent_change",
                "title": "최근 관찰 흐름",
                "format": "paragraph",
                "content": (
                    "저장된 관찰값은 최근 일주일 비교에서 낮아졌으며, 수치는 이슈의 실제 "
                    "결과가 아닌 참여 데이터의 변화 범위를 보여줍니다."
                ),
                "items": [],
                "evidence_refs": ["metric:42"],
            },
        ],
    }


def test_v8_prompt_centers_issue_flow_and_keeps_exact_evidence_bundle():
    system, user = build_v8_prompt(_inputs())
    payload = json.loads(user)

    assert "작성의 중심은 데이터가 아니라" in system
    assert "이슈입니다" in system
    assert "시장 수치나 데이터 종류를 중심으로 보고서를 구성하지 마십시오" in system
    assert "모든 문장에 참조를 붙이지 말고 섹션 단위로 연결합니다" in system
    assert "다음 표현은 어떤 문맥에서도" in system
    assert "확정" in system
    assert "명시적 부정·한계·여부 확인" in system
    assert payload["policy_version"] == "v8-contextual-wording-1"
    assert payload["input_schema_version"] == "v8-writer-stream-input-1"
    assert payload["allowed_section_types"] == [
        "current_situation",
        "recent_change",
        "interpretation",
        "key_conditions",
        "what_to_watch",
        "limitations",
    ]
    assert [item["ref"] for item in payload["evidence"]] == [
        "market_definition:rule-1",
        "metric:42",
        "context:ctx-1",
        "source:src-1",
    ]


def test_v8_stream_prompt_and_line_parser_use_strict_ndjson_blocks():
    system, user = build_v8_stream_prompt(_inputs())
    payload = json.loads(user)

    assert "각 JSON 객체는 반드시 한 줄" in system
    assert payload["required_output_shape"]["protocol"].startswith("NDJSON")
    header = parse_v8_stream_line(
        json.dumps(
            {
                "kind": "headline_summary",
                "headline": _raw_output()["headline"],
                "summary": _raw_output()["summary"],
            },
            ensure_ascii=False,
        )
    )
    section = parse_v8_stream_line(
        json.dumps(
            {"kind": "section", "index": 0, "section": _raw_output()["sections"][0]},
            ensure_ascii=False,
        )
    )
    complete = parse_v8_stream_line('{"kind":"complete","section_count":2}')

    assert isinstance(header, V8StreamHeadlineBlock)
    assert isinstance(section, V8StreamSectionBlock)
    assert isinstance(complete, V8StreamCompleteBlock)
    assert validate_v8_stream_block(header, _inputs(), []).passed
    assert validate_v8_stream_block(section, _inputs(), []).passed
    assert parse_v8_stream_line('{"kind":"section","index":0}') is None


def test_v8_valid_issue_centered_output_parses_and_passes():
    parsed = parse_v8_writer_output(json.dumps(_raw_output(), ensure_ascii=False))

    assert parsed is not None
    assert validate_v8_writer_output(parsed, _inputs()).passed


def test_v8_requires_source_parent_reference_in_same_section():
    raw = _raw_output()
    raw["sections"][0]["evidence_refs"] = [
        "market_definition:rule-1",
        "source:src-1",
    ]
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    result = validate_v8_writer_output(parsed, _inputs())
    assert not result.passed
    assert result.rule == "source_parent_ref_missing"


def test_v8_rejects_duplicate_section_types():
    raw = _raw_output()
    raw["sections"][1]["type"] = "current_situation"

    assert parse_v8_writer_output(json.dumps(raw, ensure_ascii=False)) is None


def test_v8_rejects_unattributed_positive_certainty():
    raw = _raw_output()
    raw["sections"][0]["content"] = (
        "의회가 다음 회기에 열리는 것이 확정됐으며 관련 절차도 이어질 예정입니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    result = validate_v8_writer_output(parsed, _inputs())
    assert not result.passed
    assert result.rule == "contextual_phrase_unattributed:확정"


def test_v8_allows_explicit_negation_and_verification_inquiry_without_source():
    raw = _raw_output()
    raw["summary"] = (
        "이 이슈는 의회 해산 조건을 확인합니다. 현재 자료는 일정과 관찰값만 담고 "
        "있으며 해산이 확정됐다는 뜻은 아닙니다. 공식 발표에서 확정 여부를 다시 "
        "확인해야 하고 현재 수치는 실제 결과와 구분해서 읽어야 합니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    assert validate_v8_writer_output(parsed, _inputs()).passed


def test_v8_allows_source_supported_attributed_certainty():
    raw = _raw_output()
    raw["sections"][0]["content"] = (
        "기관 공식 문서에는 의회가 다음 회기에 열리는 것이 확정됐다고 명시되어 "
        "있으며, 해당 문서의 일정 범위에서만 이 사실을 확인할 수 있습니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    assert validate_v8_writer_output(parsed, _inputs()).passed


def test_v8_rejects_attribution_when_source_claim_lacks_same_strength_marker():
    inputs = _inputs()
    inputs.evidence[-1].text = "기관 공식 일정 문서에는 회의 날짜만 기록되어 있습니다."
    raw = _raw_output()
    raw["sections"][0]["content"] = (
        "기관 공식 문서에는 의회가 다음 회기에 열리는 것이 확정됐다고 명시되어 "
        "있으며, 해당 문서의 일정 범위에서만 이 사실을 확인할 수 있습니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    result = validate_v8_writer_output(parsed, inputs)
    assert not result.passed
    assert result.rule == "contextual_phrase_unsupported:확정"


def test_v8_contextual_recommendation_requires_attribution_and_source_support():
    raw = _raw_output()
    raw["sections"][0]["content"] = (
        "위원회 보고서는 해당 일정을 추천했다고 밝혔으며, 문서가 제시한 절차 "
        "범위에서만 이 권고 내용을 확인할 수 있습니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))
    assert parsed is not None
    assert validate_v8_writer_output(parsed, _inputs()).passed

    raw["sections"][0]["content"] = (
        "이 일정은 사용자에게 추천할 만한 선택이며 앞으로도 계속 확인해야 합니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))
    assert parsed is not None
    result = validate_v8_writer_output(parsed, _inputs())
    assert not result.passed
    assert result.rule == "contextual_phrase_unattributed:추천"


@pytest.mark.parametrize(
    "sentence",
    [
        "기관 공식 문서에는 발언권이 보장된다고 명시되어 있으며 문서 범위에서만 확인합니다.",
        "위원회 보고서는 의견 제출 기회를 제공한다고 밝혔으며 절차 범위에서만 확인합니다.",
        "기관 공식 보고서는 일정 준수 전망을 제시했다고 밝혔으며 자료 범위에서만 인용합니다.",
        (
            "기관 공식 보고서는 일정 변경의 원인이 절차 지연이라고 밝혔으며 "
            "출처 주장으로만 인용합니다."
        ),
    ],
)
def test_v8_allows_other_source_supported_contextual_terms(sentence):
    raw = _raw_output()
    raw["sections"][0]["content"] = sentence
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    assert validate_v8_writer_output(parsed, _inputs()).passed


@pytest.mark.parametrize(
    "safe_phrase",
    [
        "전체 대중을 대표한다고 보장하지 않습니다",
        "사용자 행동의 기회로 제시하지 않습니다",
        "실제 결과에 대한 전망이 아닙니다",
        "관찰 변화의 원인이 아닙니다",
    ],
)
def test_v8_allows_other_explicit_negative_contexts_without_source(safe_phrase):
    raw = _raw_output()
    raw["summary"] = (
        "이 이슈는 저장된 정의와 관찰 자료의 범위만 설명합니다. "
        f"이 문장은 {safe_phrase}. "
        "현재 수치는 실제 사건의 결과가 아니라 공개 데이터에 나타난 흐름이며 "
        "공식 자료를 통해 별도로 확인해야 합니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    assert validate_v8_writer_output(parsed, _inputs()).passed


def test_v8_keeps_future_outcome_assertions_blocked():
    raw = _raw_output()
    raw["sections"][0]["content"] = (
        "현재 일정이 공개되어 있으며 의회는 다음 달 반드시 해산할 것이다. "
        "이 문장은 제공된 자료의 범위를 넘어 실제 결과를 단정합니다."
    )
    parsed = parse_v8_writer_output(json.dumps(raw, ensure_ascii=False))

    assert parsed is not None
    result = validate_v8_writer_output(parsed, _inputs())
    assert not result.passed
    assert result.rule == "unsafe_language:할\\s*것이다"
