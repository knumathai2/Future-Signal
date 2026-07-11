"""ADR-051 v7 positive-first writer contract tests."""

import json
import uuid

import pytest
from pydantic import ValidationError

from app.core.ai_report import (
    V7EvidenceItem,
    V7WriterInputs,
    build_v7_prompt,
    parse_v7_writer_output,
    validate_v7_writer_output,
)

ISSUE_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


def _inputs() -> V7WriterInputs:
    return V7WriterInputs(
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
                text="현재 공개 데이터 값과 최근 변화가 기록되어 있습니다.",
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
        "headline": "공식 결정 조건과 현재 공개 자료 요약",
        "summary": (
            "이 이슈는 공식 문서에 결정이 기록되는지를 살펴보며, 현재 공개 자료와 "
            "외부 문서가 각각 어떤 내용을 보여주는지 구분해 정리합니다."
        ),
        "sections": [
            {
                "type": "issue_overview",
                "title": "이슈의 기준",
                "format": "paragraph",
                "content": "공식 문서에 정해진 결정이 기록되는지가 이 이슈의 핵심 확인 대상입니다.",
                "items": [],
                "evidence_refs": ["market_definition:rule-1"],
            },
            {
                "type": "external_context",
                "title": "확인된 공개 문서",
                "format": "bullets",
                "content": None,
                "items": ["기관이 공개한 일정 문서에는 관련 절차의 예정 순서가 담겨 있습니다."],
                "evidence_refs": ["context:ctx-1", "source:src-1"],
            },
        ],
    }


def test_v7_prompt_is_positive_first_and_exposes_exact_evidence_refs():
    system, user = build_v7_prompt(_inputs())
    payload = json.loads(user)

    assert system.startswith("You are an issue briefing writer")
    assert "Do not write any digits" not in system
    assert "판정, 조건 충족 여부, 공식 결정" in system
    assert "supplied comparison window" in system
    assert "current_value_percent" in system
    assert "calculating a new value" in system
    assert payload["policy_version"] == "v7-positive-evidence-1"
    assert [item["ref"] for item in payload["evidence"]] == [
        "market_definition:rule-1",
        "metric:42",
        "context:ctx-1",
        "source:src-1",
    ]


def test_v7_valid_flexible_output_parses_and_passes():
    parsed = parse_v7_writer_output(json.dumps(_raw_output(), ensure_ascii=False))
    assert parsed is not None
    assert validate_v7_writer_output(parsed, _inputs()).passed


@pytest.mark.parametrize(
    ("mutation", "expected_rule"),
    [
        (
            lambda raw: raw["sections"][1].update(evidence_refs=["source:src-1"]),
            "source_parent_ref_missing",
        ),
        (
            lambda raw: raw["sections"][0].update(evidence_refs=["metric:missing"]),
            "unknown_evidence_ref",
        ),
        (lambda raw: raw.update(headline="추천 결과를 확인하는 상세 브리핑"), "banned_phrase:추천"),
        (
            lambda raw: raw["sections"][0].update(
                content="공식 주소 https://example.com 을 확인하는 충분히 긴 설명입니다."
            ),
            "writer_added_url",
        ),
    ],
)
def test_v7_blocking_validation(mutation, expected_rule):
    raw = _raw_output()
    mutation(raw)
    parsed = parse_v7_writer_output(json.dumps(raw, ensure_ascii=False))
    assert parsed is not None
    result = validate_v7_writer_output(parsed, _inputs())
    assert not result.passed
    assert result.rule == expected_rule


def test_v7_output_rejects_extra_fields_and_invalid_format_shape():
    raw = _raw_output()
    raw["extra"] = True
    assert parse_v7_writer_output(json.dumps(raw, ensure_ascii=False)) is None

    raw = _raw_output()
    raw["sections"][0]["items"] = ["문단 형식에는 목록이 함께 들어갈 수 없습니다."]
    assert parse_v7_writer_output(json.dumps(raw, ensure_ascii=False)) is None


def test_v7_input_rejects_unlinked_source_and_duplicate_refs():
    with pytest.raises(ValidationError):
        V7WriterInputs(
            issue_id=ISSUE_ID,
            title="이슈",
            category="정치",
            evidence=[
                V7EvidenceItem(
                    ref="market_definition:r",
                    kind="market_definition",
                    text="정의",
                ),
                V7EvidenceItem(ref="metric:1", kind="metric", text="지표"),
                V7EvidenceItem(
                    ref="source:s",
                    kind="source",
                    text="출처",
                    parent_ref="context:missing",
                    source_level="B",
                ),
            ],
        )
