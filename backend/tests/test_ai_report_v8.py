"""TASK-112 v8 issue-centered writer contract tests."""

import json
import uuid

from app.core.ai_report import (
    V7EvidenceItem,
    V8WriterInputs,
    build_v8_prompt,
    parse_v8_writer_output,
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
                text="기관 공식 일정 문서",
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
    assert payload["policy_version"] == "v8-issue-centered-1"
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
