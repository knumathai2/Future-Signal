"""ADR-050 v6 mode selection, strict authored shapes, and safety gates."""

import json
import uuid
from datetime import UTC, datetime

import pytest

from app.core.ai_report import (
    ResolutionRulesInput,
    V4ContextSource,
    V4ReportInputs,
    V4VerifiedCandidateInput,
    V6ChangeWithEvidenceBriefing,
    V6ChangeWithoutEvidenceBriefing,
    V6StableWithEvidenceBriefing,
    V6StableWithoutEvidenceBriefing,
    build_v6_prompt,
    build_v6_stored_payload,
    determine_v6_report_mode,
    parse_v6_briefing,
    run_v6_safety_and_semantic_checks,
)

NOW = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
CANDIDATE_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def _candidate() -> V4VerifiedCandidateInput:
    return V4VerifiedCandidateInput(
        id=CANDIDATE_ID,
        title="공식 성명 공개",
        event_at=datetime(2026, 7, 11, 8, 0, tzinfo=UTC),
        neutral_summary="정부 기관이 대통령직 관련 공개 성명을 게시했습니다.",
        sources=[
            V4ContextSource(
                citation_id="citation:a",
                title="정부 기관 공개 성명",
                url="https://example.gov/statement",
                canonical_url="https://example.gov/statement",
                domain="example.gov",
                source_type="official",
                content_hash="sha256:source",
            )
        ],
    )


def _inputs(*, changed: bool, with_evidence: bool, **overrides) -> V4ReportInputs:
    values = {
        "market_id": uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
        "metric_id": 123,
        "episode_at": NOW,
        "data_as_of": NOW,
        "title": "대통령직 사임 이슈",
        "description": "대통령직 변동 조건을 다루는 공개 데이터 이슈입니다.",
        "category": "정치",
        "outcome_label": "Yes",
        "end_date": datetime(2026, 12, 31, tzinfo=UTC),
        "current_value": 0.055,
        "change_24h": 0.05 if changed else 0.01,
        "change_7d": 0.02,
        "confidence_level": "sufficient",
        "volume_24h": 1000.0,
        "liquidity": 2000.0,
        "context_candidates": [_candidate()] if with_evidence else [],
        "resolution_rules": ResolutionRulesInput(
            condition_text="대통령이 기준일까지 공식 사임서를 제출하면 조건을 충족합니다.",
            deadline=datetime(2026, 12, 31, tzinfo=UTC),
            exclusions=["임시 권한 이양은 포함하지 않습니다."],
            resolution_source=None,
            source_description_hash="source-hash",
            rules_hash="rules-hash",
            collected_at=datetime(2026, 7, 11, 7, 0, tzinfo=UTC),
        ),
    }
    values.update(overrides)
    return V4ReportInputs(**values)


def _raw_briefing(mode: str) -> dict:
    scenario = {
        "title": "제도 변화가 논의되는 경우",
        "text": (
            "만약 대통령직 변동 논의가 이어지는 경우 관련 기관의 공개 자료가 "
            "어떤 범위를 다루는지 살펴볼 수 있습니다."
        ),
        "basis": "general_scenario",
    }
    material = {
        "scenario_index": 1,
        "title": "공개 문서 범위",
        "text": "대통령직 변동 논의를 다루는 공식 공개 문서의 범위를 확인할 자료입니다.",
        "basis": "general_scenario",
    }
    verified = {
        "text": (
            "정부 기관 공개 성명은 대통령직 관련 내용을 담고 있으며, 관찰된 흐름과의 "
            "관계를 입증하지 않는 공개 배경입니다."
        ),
        "basis": "verified_context",
        "candidate_ids": [str(CANDIDATE_ID)],
    }
    if mode == "change_with_evidence":
        return {
            "mode": mode,
            "verified_background": verified,
            "conditional_interpretations": [
                {
                    "title": "성명 범위가 이어지는 경우",
                    "text": (
                        "만약 후속 공개 자료가 같은 대통령직 주제를 다루는 경우 성명의 "
                        "적용 범위를 조건부로 비교할 수 있습니다."
                    ),
                    "basis": "verified_context",
                    "candidate_ids": [str(CANDIDATE_ID)],
                }
            ],
        }
    if mode == "change_without_evidence":
        return {
            "mode": mode,
            "conditional_scenarios": [scenario],
            "materials_to_check": [material],
        }
    if mode == "stable_with_evidence":
        return {
            "mode": mode,
            "issue_explanation": {
                "text": (
                    "이 이슈는 대통령직 변동이 공적 기록에서 어떻게 다뤄지는지를 "
                    "살펴보는 항목입니다."
                ),
                "basis": "market_definition",
            },
            "verified_background": verified,
            "conditional_scenarios": [scenario],
        }
    return {
        "mode": mode,
        "issue_explanation": {
            "text": (
                "이 이슈는 대통령직 변동 논의를 이해하기 위한 일반적인 상황 구분을 "
                "다루는 항목입니다."
            ),
            "basis": "general_scenario",
        },
        "conditional_scenarios": [scenario],
        "materials_to_check": [material],
    }


@pytest.mark.parametrize(
    ("changed", "with_evidence", "expected"),
    [
        (True, True, "change_with_evidence"),
        (True, False, "change_without_evidence"),
        (False, True, "stable_with_evidence"),
        (False, False, "stable_without_evidence"),
    ],
)
def test_mode_is_selected_deterministically(changed, with_evidence, expected):
    assert (
        determine_v6_report_mode(_inputs(changed=changed, with_evidence=with_evidence)) == expected
    )


def test_insufficient_metric_never_selects_change_mode():
    inputs = _inputs(
        changed=True,
        with_evidence=False,
        confidence_level="insufficient_data",
    )
    assert determine_v6_report_mode(inputs) == "stable_without_evidence"


@pytest.mark.parametrize(
    ("mode", "briefing_type"),
    [
        ("change_with_evidence", V6ChangeWithEvidenceBriefing),
        ("change_without_evidence", V6ChangeWithoutEvidenceBriefing),
        ("stable_with_evidence", V6StableWithEvidenceBriefing),
        ("stable_without_evidence", V6StableWithoutEvidenceBriefing),
    ],
)
def test_each_mode_parses_only_its_allowed_shape(mode, briefing_type):
    parsed = parse_v6_briefing(json.dumps(_raw_briefing(mode)), mode)
    assert isinstance(parsed, briefing_type)

    wrong_mode = (
        "stable_without_evidence"
        if mode != "stable_without_evidence"
        else "change_without_evidence"
    )
    assert parse_v6_briefing(json.dumps(_raw_briefing(mode)), wrong_mode) is None

    extra = _raw_briefing(mode)
    extra["unexpected"] = "blocked"
    assert parse_v6_briefing(json.dumps(extra), mode) is None


@pytest.mark.parametrize(
    ("changed", "with_evidence"),
    [(True, True), (True, False), (False, True), (False, False)],
)
def test_valid_mode_payload_passes_all_v6_gates(changed, with_evidence):
    inputs = _inputs(changed=changed, with_evidence=with_evidence)
    mode = determine_v6_report_mode(inputs)
    briefing = parse_v6_briefing(json.dumps(_raw_briefing(mode)), mode)
    assert briefing is not None
    payload = build_v6_stored_payload(inputs, briefing)
    assert payload is not None
    assert run_v6_safety_and_semantic_checks(payload, inputs, briefing).passed


def test_prompt_excludes_metrics_and_exact_resolution_rule():
    inputs = _inputs(changed=True, with_evidence=False)
    _system, user = build_v6_prompt(inputs)
    assert '"selected_report_mode":"change_without_evidence"' in user
    assert "0.055" not in user
    assert "0.05" not in user
    assert inputs.resolution_rules is not None
    assert inputs.resolution_rules.condition_text not in user


def test_prompt_requires_exact_issue_anchor_for_cross_language_specificity():
    inputs = _inputs(
        changed=False,
        with_evidence=False,
        title="Will Trump resign?",
        category="Politics",
    )
    system, user = build_v6_prompt(inputs)
    decoded = json.loads(user)

    assert decoded["required_issue_anchors"] == ["Trump"]
    assert "Copy at least one value from required_issue_anchors exactly" in system
    assert inputs.resolution_rules is not None
    assert inputs.resolution_rules.condition_text not in user


def test_prompt_anchor_excludes_month_and_generic_english_terms():
    inputs = _inputs(
        changed=True,
        with_evidence=False,
        title="Israeli parliament dissolved by July 31?",
        category="Politics",
    )

    _system, user = build_v6_prompt(inputs)

    assert json.loads(user)["required_issue_anchors"] == ["Israeli"]


def test_prompt_makes_scenario_material_mapping_explicit():
    inputs = _inputs(changed=True, with_evidence=False)
    system, user = build_v6_prompt(inputs)
    constraints = json.loads(user)["generation_constraints"]

    assert constraints["scenario_count_range"] == [1, 4]
    assert "exactly one" in constraints["material_mapping"]
    assert "scenario_index" in constraints["material_mapping"]
    assert "each one-based" in constraints["material_mapping"]
    assert "return exactly N materials" in system


def test_exact_english_anchor_keeps_korean_briefing_issue_specific():
    inputs = _inputs(
        changed=False,
        with_evidence=False,
        title="Will Trump resign?",
        category="Politics",
    )
    raw = _raw_briefing("stable_without_evidence")
    raw["issue_explanation"]["text"] = (
        "이 항목은 Trump 대통령직 변화 논의를 일반적인 조건부 상황으로 구분해 "
        "살펴보기 위한 설명입니다."
    )

    result = _checked_payload(raw, inputs)

    assert result.passed


def test_translated_generic_text_without_required_anchor_remains_rejected():
    inputs = _inputs(
        changed=False,
        with_evidence=False,
        title="Will Trump resign?",
        category="Politics",
    )
    raw = _raw_briefing("stable_without_evidence")
    raw["issue_explanation"]["text"] = (
        "이 항목은 대통령직 변화 논의를 일반적인 조건부 상황으로 구분해 "
        "살펴보기 위한 설명입니다."
    )

    result = _checked_payload(raw, inputs)

    assert not result.passed
    assert result.rule == "generic_summary"


def test_authored_english_month_is_rejected_even_without_digits():
    inputs = _inputs(
        changed=False,
        with_evidence=False,
        title="Will Trump resign?",
        category="Politics",
    )
    raw = _raw_briefing("stable_without_evidence")
    raw["issue_explanation"]["text"] = (
        "Trump 대통령직 변화 이슈를 december 시점과 연결해 설명하는 일반 항목입니다."
    )

    result = _checked_payload(raw, inputs)

    assert not result.passed
    assert result.rule == "authored_date_repeated"


def test_generic_english_term_outside_exact_anchor_is_rejected():
    inputs = _inputs(
        changed=False,
        with_evidence=False,
        title="Will Trump resign?",
        category="Politics",
    )
    raw = _raw_briefing("stable_without_evidence")
    raw["issue_explanation"]["text"] = (
        "Trump 대통령직의 resign 표현을 일반적인 조건부 상황으로 구분해 살펴보는 항목입니다."
    )

    result = _checked_payload(raw, inputs)

    assert not result.passed
    assert result.rule == "non_korean_generic_term"


def _checked_payload(raw: dict, inputs: V4ReportInputs):
    mode = determine_v6_report_mode(inputs)
    briefing = parse_v6_briefing(json.dumps(raw), mode)
    assert briefing is not None
    payload = build_v6_stored_payload(inputs, briefing)
    assert payload is not None
    return run_v6_safety_and_semantic_checks(payload, inputs, briefing)


def test_metric_number_in_authored_text_is_rejected():
    inputs = _inputs(changed=True, with_evidence=False)
    raw = _raw_briefing("change_without_evidence")
    raw["conditional_scenarios"][0]["text"] += " 현재 값은 5.5퍼센트입니다."
    result = _checked_payload(raw, inputs)
    assert not result.passed
    assert result.rule == "deterministic_value_repeated"


def test_resolution_rule_repetition_is_rejected():
    inputs = _inputs(changed=False, with_evidence=False)
    raw = _raw_briefing("stable_without_evidence")
    assert inputs.resolution_rules is not None
    raw["issue_explanation"]["text"] = inputs.resolution_rules.condition_text
    result = _checked_payload(raw, inputs)
    assert not result.passed
    assert result.rule == "resolution_rule_repeated"


def test_same_body_with_different_title_is_rejected():
    inputs = _inputs(changed=False, with_evidence=False)
    raw = _raw_briefing("stable_without_evidence")
    raw["conditional_scenarios"].append(
        {
            "title": "다른 제목",
            "text": raw["conditional_scenarios"][0]["text"],
            "basis": "general_scenario",
        }
    )
    result = _checked_payload(raw, inputs)
    assert not result.passed
    assert result.rule == "duplicate_narrative_fields"


def test_source_free_recent_fact_is_rejected():
    inputs = _inputs(changed=False, with_evidence=False)
    raw = _raw_briefing("stable_without_evidence")
    raw["issue_explanation"]["text"] = (
        "최근 대통령직 관련 기관이 새 결정을 발표했습니다. 이 이슈는 그 내용을 다룹니다."
    )
    result = _checked_payload(raw, inputs)
    assert not result.passed
    assert result.rule == "unsupported_current_fact"


def test_unverified_candidate_ids_are_rejected():
    inputs = _inputs(changed=True, with_evidence=True)
    raw = _raw_briefing("change_with_evidence")
    raw["verified_background"]["candidate_ids"] = ["cccccccc-cccc-4ccc-8ccc-cccccccccccc"]
    result = _checked_payload(raw, inputs)
    assert not result.passed
    assert result.rule == "candidate_id_mismatch"


def test_each_scenario_requires_a_matching_material():
    inputs = _inputs(changed=True, with_evidence=False)
    raw = _raw_briefing("change_without_evidence")
    raw["conditional_scenarios"].append(
        {
            "title": "별도 문서가 나오는 경우",
            "text": (
                "만약 대통령직 관련 별도 공개 문서가 나오는 경우 문서가 다루는 "
                "상황의 범위를 구분할 수 있습니다."
            ),
            "basis": "general_scenario",
        }
    )
    result = _checked_payload(raw, inputs)
    assert not result.passed
    assert result.rule == "scenario_material_mismatch"
