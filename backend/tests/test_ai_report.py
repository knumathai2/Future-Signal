"""TASK-049: ADR-033 v3 build_prompt(), the strict LLM-field parse,
deterministic field assembly, the banned-phrase/pattern safety filter, and
the cross-field semantic checks. Pure logic - no database needed; the
regeneration/storage orchestration lives in test_ai_report_batch.py.
"""

import json
import uuid
from datetime import UTC, datetime

import httpx
import openai
import pytest

from app.core.ai_report import (
    CAUTION_NOTE_BY_LEVEL,
    POSSIBLE_DRIVERS_NO_CANDIDATE,
    POSSIBLE_DRIVERS_WITH_CANDIDATE,
    SYSTEM_PROMPT,
    LLMCallError,
    LLMReportFields,
    OpenAIReportClient,
    ReportContent,
    ReportPromptInputs,
    ResolutionRulesInput,
    V4ContextSource,
    V4LLMFields,
    V4ReportInputs,
    V4VerifiedCandidateInput,
    V5LLMFields,
    assemble_report_content,
    assemble_v4_report_content,
    assemble_v5_report_content,
    build_caution_note,
    build_data_limitations,
    build_external_context,
    build_openai_client,
    build_possible_drivers,
    build_prompt,
    build_v4_prompt,
    build_v4_stored_payload,
    build_v5_prompt,
    build_v5_stored_payload,
    build_what_to_check,
    determine_input_completeness,
    parse_llm_fields,
    parse_v4_llm_fields,
    parse_v5_llm_fields,
    run_safety_filter,
    run_semantic_checks,
    run_v4_safety_and_semantic_checks,
    run_v5_safety_and_semantic_checks,
)
from app.core.config import (
    OPENROUTER_BASE_URL,
    _resolve_ai_base_url,
    _resolve_ai_model,
    _resolve_ai_provider,
)

VALID_LLM_FIELDS = {
    "issue_overview": "이 이슈는 공개된 기한까지 문서에 적힌 조건이 충족되는지를 추적합니다.",
    "current_data_reading": (
        "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 63%이며, "
        "24시간 전보다 8.0퍼센트포인트 높게 관찰되었습니다."
    ),
    "possible_outlook": (
        "이후 공개 데이터에서 관찰된 움직임의 지속, 확대 또는 완화가 확인되더라도, "
        "이는 데이터의 흐름만 설명하며 현실의 결과나 변화의 이유를 입증하지 않습니다."
    ),
}


def _inputs(**overrides) -> ReportPromptInputs:
    base = dict(
        title="Will the test issue resolve Yes?",
        description="A seeded test issue.",
        category="technology",
        outcome_label="Yes",
        end_date=datetime(2026, 12, 31, tzinfo=UTC),
        current_value=0.63,
        change_24h=0.08,
        change_7d=0.11,
        confidence_level="sufficient",
        inflection_point_summary="A +8.0pp expectation shift was detected in the 24h window.",
        volume_24h=1000.0,
        liquidity=2000.0,
        related_event_title=None,
        related_event_date=None,
        related_event_note=None,
    )
    base.update(overrides)
    return ReportPromptInputs(**base)


def _reviewed_candidate_inputs(**overrides) -> ReportPromptInputs:
    base = dict(
        related_event_title="Kraken Files Initial Registration Statement Draft",
        related_event_date=datetime(2026, 2, 18, tzinfo=UTC),
        related_event_note=(
            "A draft registration statement was submitted. Candidate context "
            "entered manually for review alongside the observed change; not "
            "presented as a cause."
        ),
    )
    base.update(overrides)
    return _inputs(**base)


def _llm_fields(**overrides) -> LLMReportFields:
    base = dict(VALID_LLM_FIELDS)
    base.update(overrides)
    return LLMReportFields(**base)


def _v4_inputs(*, with_context=True, **overrides) -> V4ReportInputs:
    candidates = []
    if with_context:
        candidates = [
            V4VerifiedCandidateInput(
                id=uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
                title="공개 정보 업데이트",
                event_at=datetime(2026, 7, 11, 8, 0, tzinfo=UTC),
                neutral_summary="두 공개 출처는 해당 시각에 관련 정보를 기록했습니다.",
                sources=[
                    V4ContextSource(
                        citation_id="citation:a",
                        title="공개 출처",
                        url="https://example.gov/update",
                        canonical_url="https://example.gov/update",
                        domain="example.gov",
                        source_type="official",
                        content_hash="sha256:source",
                    )
                ],
            )
        ]
    values = {
        "market_id": uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
        "metric_id": 123,
        "episode_at": datetime(2026, 7, 11, 8, 0, tzinfo=UTC),
        "data_as_of": datetime(2026, 7, 11, 9, 0, tzinfo=UTC),
        "title": "Will JD Vance win the US Presidential Election?",
        "description": "Tracks whether JD Vance wins the documented election.",
        "category": "technology",
        "outcome_label": "Yes",
        "end_date": datetime(2026, 12, 31, tzinfo=UTC),
        "current_value": 0.63,
        "change_24h": 0.08,
        "change_7d": 0.11,
        "confidence_level": "sufficient",
        "volume_24h": 1000.0,
        "liquidity": 2000.0,
        "context_candidates": candidates,
        "resolution_rules": ResolutionRulesInput(
            condition_text="The documented condition is recorded by the deadline.",
            deadline=datetime(2026, 12, 31, tzinfo=UTC),
            exclusions=[],
            resolution_source=None,
            source_description_hash="default-description-hash",
            rules_hash="default-rules-hash",
            collected_at=datetime(2026, 7, 11, 7, 0, tzinfo=UTC),
        ),
    }
    values.update(overrides)
    return V4ReportInputs(**values)


def _v4_fields(**overrides) -> V4LLMFields:
    values = {
        "issue_overview": (
            "이 이슈는 문서에 적힌 조건이 정해진 기준 안에서 확인되는지를 살펴봅니다."
        ),
        "what_to_check": (
            "게시된 조건 문구와 이후 공개되는 자료 및 데이터 갱신 내용을 추가로 확인해야 합니다."
        ),
    }
    values.update(overrides)
    return V4LLMFields(**values)


def _v5_fields(*, with_context=True, **overrides) -> V5LLMFields:
    values = {
        "executive_summary": (
            "Will JD Vance win the US Presidential Election? 질문의 문서 조건을 다루는 "
            "이슈입니다. 공개 데이터에 "
            "저장된 현재 값과 최근 비교 구간의 움직임을 함께 읽되 현실의 결과로 해석하지 않습니다."
        ),
        "current_data_interpretation": (
            "저장된 현재 값과 최근 비교값은 참여자 데이터의 관찰 흐름을 보여줍니다. "
            "이 움직임만으로 현실의 결과나 배경을 판단할 수 없습니다."
        ),
        "conditional_scenarios": [
            {
                "title": "조건 확인",
                "narrative": (
                    "만약 JD Vance의 당선 조건이 공식 선거 문서에서 확인된다면 "
                    "해당 판정 조건과 함께 읽습니다."
                ),
            },
            {
                "title": "부분 확인",
                "narrative": (
                    "만약 JD Vance 관련 문서가 공개되지만 당선 조건을 충족하는지 "
                    "불분명한 경우 추가 문서를 확인합니다."
                ),
            },
            {
                "title": "조건 미확인",
                "narrative": (
                    "만약 기준일까지 JD Vance의 당선 조건이 공식 문서에서 "
                    "확인되지 않는다면 미확인 상태로 구분합니다."
                ),
            },
        ],
        "factors_to_check": [
            {
                "title": "판정 문서",
                "explanation": "JD Vance와 선거 결과를 명시한 공식 문서의 조건을 확인합니다.",
            },
            {
                "title": "기준 시각",
                "explanation": "문서가 이 이슈의 정해진 기준일 안에 공개됐는지 확인합니다.",
            },
        ],
        "signals_to_watch": [
            {
                "title": "공식 문서 공개",
                "explanation": "JD Vance 관련 공식 선거 문서의 공개 여부를 관찰합니다.",
            },
            {
                "title": "데이터 갱신",
                "explanation": "공개 예측시장 데이터의 이후 갱신 시각과 값을 별도로 확인합니다.",
            },
        ],
        "evidence_synthesis": (
            "같은 검토 구간의 공개 정보 업데이트는 해당 조건과 관련된 기록을 제공합니다. "
            "이 자료와 관찰된 움직임 사이의 관계는 확인되지 않았습니다."
            if with_context
            else None
        ),
    }
    values.update(overrides)
    return V5LLMFields(**values)


# --- build_prompt -------------------------------------------------------


def test_build_prompt_returns_fixed_system_prompt_verbatim():
    system_prompt, _ = build_prompt(_inputs())
    assert system_prompt == SYSTEM_PROMPT


def test_build_prompt_states_every_adr_033_llm_field_length_bound():
    system_prompt, user_prompt = build_prompt(_inputs())

    assert "issue_overview 30-600 characters" in system_prompt
    assert "current_data_reading 50-700" in system_prompt
    assert "possible_outlook 60-700 characters" in system_prompt
    assert "issue_overview: 30-600 characters" in user_prompt
    assert "current_data_reading: 50-700 characters" in user_prompt
    assert 'includes the exact Korean phrase\n  "공개 예측시장 참여자 데이터"' in user_prompt
    assert "possible_outlook: 60-700 characters" in user_prompt


def test_build_prompt_requires_the_safety_filter_approved_korean_source_compound():
    system_prompt, _ = build_prompt(_inputs())

    assert 'exact no-space compound\n  "공개 예측시장 참여자 데이터"' in system_prompt
    assert 'Never write "예측 시장" with a space' in system_prompt


def test_build_prompt_fills_only_the_named_slots():
    _, user_prompt = build_prompt(_inputs())

    assert "Will the test issue resolve Yes?" in user_prompt
    assert "A seeded test issue." in user_prompt
    assert "technology" in user_prompt
    assert "63.0%" in user_prompt
    assert "+8.0pp" in user_prompt
    assert "+11.0pp" in user_prompt
    assert "sufficient" in user_prompt
    # the fixed instruction footer is present verbatim (never trimmed/altered)
    assert '"issue_overview": "..."' in user_prompt
    assert '"current_data_reading": "..."' in user_prompt
    assert '"possible_outlook": "..."' in user_prompt


def test_build_prompt_never_exposes_related_event_to_the_llm():
    """ADR-033 design: possible_drivers/external_context are deterministic,
    never LLM prose, so the candidate must never reach the prompt at all."""
    _, user_prompt = build_prompt(_reviewed_candidate_inputs())
    assert "related_event" not in user_prompt.lower()
    assert "Kraken" not in user_prompt


def test_build_prompt_uses_none_placeholder_when_no_inflection_point():
    _, user_prompt = build_prompt(_inputs(inflection_point_summary=None))
    assert "Recent inflection point (if any): None" in user_prompt


def test_build_prompt_reports_missing_change_windows_as_not_available_never_zero():
    _, user_prompt = build_prompt(_inputs(change_24h=None, change_7d=None))
    assert "not available" in user_prompt
    assert "0.0pp" not in user_prompt


def test_build_prompt_reports_undocumented_end_date_and_outcome_label():
    _, user_prompt = build_prompt(_inputs(end_date=None, outcome_label=None))
    assert "No documented end date" in user_prompt
    assert "Not documented" in user_prompt


# --- parse_llm_fields -----------------------------------------------------


def test_parse_valid_json_returns_llm_fields():
    fields = parse_llm_fields(json.dumps(VALID_LLM_FIELDS))
    assert isinstance(fields, LLMReportFields)
    assert fields.issue_overview == VALID_LLM_FIELDS["issue_overview"]


def test_parse_malformed_json_returns_none():
    assert parse_llm_fields("{not valid json") is None


def test_parse_non_object_json_returns_none():
    assert parse_llm_fields("[1, 2, 3]") is None


def test_parse_missing_field_returns_none_not_partial():
    incomplete = dict(VALID_LLM_FIELDS)
    del incomplete["possible_outlook"]
    assert parse_llm_fields(json.dumps(incomplete)) is None


def test_parse_extra_field_returns_none():
    extended = dict(VALID_LLM_FIELDS, extra_field="free-form analysis the model added")
    assert parse_llm_fields(json.dumps(extended)) is None


# --- deterministic field builders ------------------------------------------


def test_possible_drivers_uses_no_candidate_literal_when_none_reviewed():
    assert build_possible_drivers(_inputs()) == POSSIBLE_DRIVERS_NO_CANDIDATE


def test_possible_drivers_uses_with_candidate_literal_when_one_is_reviewed():
    inputs = _reviewed_candidate_inputs()
    expected = POSSIBLE_DRIVERS_WITH_CANDIDATE.format(
        title="Kraken Files Initial Registration Statement Draft",
        date="2026-02-18",
    )
    assert build_possible_drivers(inputs) == expected


def test_possible_drivers_includes_reviewed_title_and_date_without_causal_claim():
    """ADR-033 requires the reviewed title/date as comparison context."""
    text = build_possible_drivers(_reviewed_candidate_inputs())
    assert "Kraken Files Initial Registration Statement Draft" in text
    assert "2026-02-18" in text
    assert "관계를 입증하지 않습니다" in text


def test_possible_drivers_states_missing_reviewed_date_without_fabricating_one():
    text = build_possible_drivers(_reviewed_candidate_inputs(related_event_date=None))
    assert "기록 날짜가 제공되지 않았습니다" in text


def test_external_context_is_null_when_no_reviewed_note_exists():
    assert build_external_context(_inputs()) is None


def test_external_context_passes_through_reviewed_note_verbatim():
    inputs = _reviewed_candidate_inputs()
    assert build_external_context(inputs) == inputs.related_event_note


def test_what_to_check_mentions_context_candidate_date_only_when_reviewed():
    without = build_what_to_check(_inputs())
    with_candidate = build_what_to_check(_reviewed_candidate_inputs())
    assert "맥락 후보" not in without
    assert "맥락 후보" in with_candidate


def test_what_to_check_uses_fixed_fallback_when_end_date_is_missing():
    text = build_what_to_check(_inputs(end_date=None))
    assert "문서에 기록된 기준일" in text


@pytest.mark.parametrize(
    "level",
    ["sufficient", "caution_low_activity", "caution_high_volatility", "insufficient_data"],
)
def test_caution_note_matches_exact_deterministic_literal_for_every_level(level):
    assert build_caution_note(level) == CAUTION_NOTE_BY_LEVEL[level]


def test_caution_note_rejects_unknown_confidence_level():
    with pytest.raises(ValueError):
        build_caution_note("not_a_real_level")


def test_data_limitations_mentions_missing_history_when_a_change_window_is_absent():
    text = build_data_limitations(_inputs(change_7d=None))
    assert "비교 지점 중 하나 이상이 없어" in text


def test_data_limitations_mentions_low_activity_when_volume_below_floor():
    text = build_data_limitations(_inputs(volume_24h=10.0))
    assert "제한된 활동이나 깊이" in text


def test_data_limitations_mentions_high_volatility_when_change_24h_is_large():
    text = build_data_limitations(_inputs(change_24h=0.2, change_7d=0.2))
    assert "안정된 흐름으로 해석하기 어렵습니다" in text


def test_data_limitations_independently_reports_every_detected_limitation_at_once():
    """A single confidence_level enum can hide other raw limitations
    (ADR-033) - data_limitations must mention all of them, not just one."""
    text = build_data_limitations(_inputs(change_7d=None, volume_24h=1.0, change_24h=0.2))
    assert "비교 지점 중 하나 이상이 없어" in text
    assert "제한된 활동이나 깊이" in text


def test_data_limitations_always_includes_representativeness_disclaimer():
    text = build_data_limitations(_inputs())
    assert "전체 대중의 판단을 대표하지 않습니다" in text


# --- assemble_report_content ------------------------------------------------


def test_assemble_report_content_produces_full_eight_field_object():
    content = assemble_report_content(_inputs(), _llm_fields())
    assert isinstance(content, ReportContent)
    assert content.issue_overview == VALID_LLM_FIELDS["issue_overview"]
    assert content.possible_drivers == POSSIBLE_DRIVERS_NO_CANDIDATE
    assert content.external_context is None
    assert content.caution_note == CAUTION_NOTE_BY_LEVEL["sufficient"]


def test_assemble_report_content_rejects_llm_field_below_minimum_length():
    content = assemble_report_content(_inputs(), _llm_fields(issue_overview="Too short."))
    assert content is None


def test_assemble_report_content_rejects_unknown_confidence_level():
    content = assemble_report_content(_inputs(confidence_level="not_a_real_level"), _llm_fields())
    assert content is None


def test_assemble_report_content_rejects_more_than_five_sentences():
    content = assemble_report_content(
        _inputs(),
        _llm_fields(
            issue_overview=(
                "첫 문장입니다. 둘째 문장입니다. 셋째 문장입니다. "
                "넷째 문장입니다. 다섯째 문장입니다. 여섯째 문장입니다."
            )
        ),
    )
    assert content is None


# --- run_safety_filter ----------------------------------------------------


def test_clean_content_passes_filter():
    content = assemble_report_content(_inputs(), _llm_fields())
    result = run_safety_filter(content)
    assert result.passed is True


def test_clean_content_with_reviewed_candidate_passes_filter():
    content = assemble_report_content(_reviewed_candidate_inputs(), _llm_fields())
    result = run_safety_filter(content)
    assert result.passed is True


@pytest.mark.parametrize(
    "field,text",
    [
        ("issue_overview", "You should buy into this issue now, it is a good bet."),
        ("current_data_reading", "Consider a long position given the trend, a solid opportunity."),
        ("possible_outlook", "This is a guaranteed high-return opportunity for a win rate boost."),
        ("what_to_check", "This is a high-return opportunity you should follow."),
    ],
)
def test_banned_phrase_is_rejected(field, text):
    content = assemble_report_content(_inputs(), _llm_fields())
    content = content.model_copy(update={field: text})
    result = run_safety_filter(content)
    assert result.passed is False
    assert result.field == field


@pytest.mark.parametrize(
    "text,field",
    [
        ("베팅을 추천합니다.", "what_to_check"),
        ("고수익 기회입니다.", "data_limitations"),
    ],
)
def test_korean_banned_phrase_is_rejected(text, field):
    content = assemble_report_content(_inputs(), _llm_fields())
    content = content.model_copy(update={field: text * 20})  # satisfy min length
    result = run_safety_filter(content)
    assert result.passed is False
    assert result.rule.startswith("banned_phrase:")


@pytest.mark.parametrize(
    "text",
    [
        "This will happen by the end of the month.",
        "You should check this issue again soon.",
        "The shift occurred because of a related event.",
        "Prices moved due to a related event candidate.",
        "The change was caused by a related event candidate.",
        "This candidate led to the observed movement.",
        "This candidate explains the movement entirely.",
    ],
)
def test_banned_pattern_is_rejected(text):
    content = assemble_report_content(_inputs(), _llm_fields())
    padded = text + " " * 5 + "추가 설명이 이어집니다." * 5  # satisfy min length
    content = content.model_copy(update={"possible_outlook": padded})
    result = run_safety_filter(content)
    assert result.passed is False
    assert result.rule.startswith("banned_pattern:")


@pytest.mark.parametrize(
    "korean_text",
    [
        "관찰된 변화는 후보 때문에 발생했습니다.",
        "이 요인이 주요 요인으로 작용했습니다.",
        "가격이 상승할 것이다.",
        "상승 가능성이 높다.",
    ],
)
def test_korean_causal_or_forecast_pattern_is_rejected(korean_text):
    content = assemble_report_content(_inputs(), _llm_fields())
    padded = korean_text + "추가 설명 문장을 덧붙여 최소 길이를 맞춥니다." * 3
    content = content.model_copy(update={"possible_outlook": padded})
    result = run_safety_filter(content)
    assert result.passed is False
    assert result.rule.startswith("banned_pattern:")


def test_approved_korean_negative_causal_disclaimer_passes_filter():
    content = assemble_report_content(_reviewed_candidate_inputs(), _llm_fields())
    content = content.model_copy(
        update={
            "external_context": (
                "수동 검토를 마친 맥락 메모는 관찰된 움직임과 함께 살펴볼 정보로만 "
                "제공되며, 변화의 원인으로 제시되지 않습니다."
            )
        }
    )
    assert run_safety_filter(content).passed is True
    assert run_semantic_checks(content, _reviewed_candidate_inputs()).passed is True


def test_substring_false_positive_is_not_rejected():
    # "belong" contains "long", "shortly" contains "short" - word-boundary
    # matching must not reject these.
    content = assemble_report_content(_inputs(), _llm_fields())
    text = (
        "This issue does not belong to a single category and may update "
        "shortly. Longer explanation continues here to satisfy minimum length "
        "requirements for this field without tripping any banned phrase."
    )
    content = content.model_copy(update={"possible_outlook": text})
    result = run_safety_filter(content)
    assert result.passed is True


# --- run_semantic_checks ----------------------------------------------------


def test_semantic_checks_pass_for_properly_assembled_content():
    inputs = _inputs()
    content = assemble_report_content(inputs, _llm_fields())
    assert run_semantic_checks(content, inputs).passed is True


def test_semantic_checks_reject_caution_note_mismatched_with_confidence_level():
    inputs = _inputs(confidence_level="insufficient_data", change_24h=None, change_7d=None)
    content = assemble_report_content(inputs, _llm_fields())
    tampered = content.model_copy(update={"caution_note": CAUTION_NOTE_BY_LEVEL["sufficient"]})
    result = run_semantic_checks(tampered, inputs)
    assert result.passed is False
    assert result.rule == "caution_note_literal_mismatch"


def test_semantic_checks_reject_possible_drivers_claiming_a_candidate_that_was_not_reviewed():
    inputs = _inputs()  # no reviewed candidate
    content = assemble_report_content(inputs, _llm_fields())
    tampered = content.model_copy(
        update={
            "possible_drivers": POSSIBLE_DRIVERS_WITH_CANDIDATE.format(
                title="Unreviewed candidate", date="2026-02-18"
            )
        }
    )
    result = run_semantic_checks(tampered, inputs)
    assert result.passed is False
    assert result.rule == "possible_drivers_literal_mismatch"


def test_semantic_checks_reject_external_context_missing_candidate_not_cause_qualifier():
    inputs = _reviewed_candidate_inputs(
        related_event_note=(
            "This is plain unreviewed narrative text with no qualifier at all, "
            "just filler content to satisfy the minimum length requirement."
        )
    )
    content = assemble_report_content(inputs, _llm_fields())
    result = run_semantic_checks(content, inputs)
    assert result.passed is False
    assert result.rule == "external_context_missing_candidate_not_cause_qualifier"


def test_semantic_checks_reject_current_data_reading_metric_mismatch():
    inputs = _inputs()
    content = assemble_report_content(
        inputs,
        _llm_fields(
            current_data_reading=(
                "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 "
                "99%로 관찰되었습니다."
            )
            * 2
        ),
    )
    result = run_semantic_checks(content, inputs)
    assert result.passed is False
    assert result.rule == "current_data_reading_metric_mismatch"


def test_semantic_checks_accept_current_data_reading_metrics_matching_inputs():
    inputs = _inputs()
    content = assemble_report_content(inputs, _llm_fields())
    assert run_semantic_checks(content, inputs).passed is True


def test_semantic_checks_reject_current_data_reading_without_public_participant_scope():
    inputs = _inputs()
    content = assemble_report_content(
        inputs,
        _llm_fields(
            current_data_reading=(
                "현재 수치는 63%이며 24시간 전보다 8.0퍼센트포인트 높게 "
                "관찰되었습니다. 이 값은 참고용으로만 살펴봐야 합니다."
            )
        ),
    )
    result = run_semantic_checks(content, inputs)
    assert result.passed is False
    assert result.rule == "current_data_reading_missing_public_participant_scope"


def test_semantic_checks_reject_nonconditional_possible_outlook():
    inputs = _inputs()
    content = assemble_report_content(
        inputs,
        _llm_fields(
            possible_outlook=(
                "이후 공개 데이터는 관찰된 흐름을 설명합니다. "
                "현실의 결과와는 구분되며 다른 자료를 통한 독립 확인이 필요합니다."
            )
        ),
    )
    result = run_semantic_checks(content, inputs)
    assert result.passed is False
    assert result.rule == "possible_outlook_missing_conditional_public_data_scope"


# --- OpenAIReportClient ----------------------------------------------------


class _RaisingChatCompletions:
    def __init__(self, exc: Exception):
        self._exc = exc

    def create(self, **kwargs):
        raise self._exc


class _StubOpenAI:
    def __init__(self, exc: Exception):
        self.chat = type("Chat", (), {"completions": _RaisingChatCompletions(exc)})()


def test_openai_client_wraps_provider_errors_as_llm_call_error():
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    stub = _StubOpenAI(openai.APITimeoutError(request))
    client = OpenAIReportClient(stub, model="gpt-4o-mini")

    with pytest.raises(LLMCallError):
        client.complete("system", "user")


class _EmptyResponseChatCompletions:
    def create(self, **kwargs):
        return type("Resp", (), {"choices": []})()


class _EmptyResponseOpenAI:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": _EmptyResponseChatCompletions()})()


def test_openai_client_raises_on_empty_response():
    client = OpenAIReportClient(_EmptyResponseOpenAI(), model="gpt-4o-mini")
    with pytest.raises(LLMCallError):
        client.complete("system", "user")


def test_openrouter_key_selects_openrouter_provider():
    provider = _resolve_ai_provider(
        provider=None,
        openrouter_api_key=None,
        openai_api_key="sk-or-v1-example",
    )

    assert provider == "openrouter"
    assert _resolve_ai_base_url(provider, raw_base_url=None) == OPENROUTER_BASE_URL
    assert _resolve_ai_model(provider, raw_model="gpt-4o-mini") == "openai/gpt-4o-mini"


def test_openrouter_model_slug_is_preserved_when_already_qualified():
    assert (
        _resolve_ai_model("openrouter", raw_model="anthropic/claude-3.5-sonnet")
        == "anthropic/claude-3.5-sonnet"
    )
    assert _resolve_ai_model("openrouter", raw_model="~openai/gpt-latest") == ("~openai/gpt-latest")


class _CapturingChatCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        message = type("Message", (), {"content": '{"ok": true}'})()
        choice = type("Choice", (), {"message": message})()
        return type("Resp", (), {"choices": [choice]})()


class _CapturingOpenAI:
    def __init__(self):
        self.completions = _CapturingChatCompletions()
        self.chat = type("Chat", (), {"completions": self.completions})()


def test_build_openai_client_passes_openrouter_base_url_and_headers(monkeypatch):
    captured_constructor_kwargs = {}
    stub = _CapturingOpenAI()

    def fake_openai(**kwargs):
        captured_constructor_kwargs.update(kwargs)
        return stub

    monkeypatch.setattr("app.core.ai_report.OpenAI", fake_openai)

    client = build_openai_client(
        "sk-or-v1-example",
        "openai/gpt-4o-mini",
        base_url=OPENROUTER_BASE_URL,
        provider_name="openrouter",
        extra_headers={"X-OpenRouter-Title": "Outlook Signals"},
    )

    assert client.complete("system", "user") == '{"ok": true}'
    assert captured_constructor_kwargs == {
        "api_key": "sk-or-v1-example",
        "base_url": OPENROUTER_BASE_URL,
    }
    assert stub.completions.kwargs["model"] == "openai/gpt-4o-mini"
    assert stub.completions.kwargs["extra_headers"] == {"X-OpenRouter-Title": "Outlook Signals"}


# --- ADR-038 v4 evidence-grounded report ---------------------------------


def test_v4_prompt_and_parser_are_strict_two_field_contract():
    system_prompt, user_prompt = build_v4_prompt(_v4_inputs())

    assert "issue_overview" in user_prompt
    assert "what_to_check" in user_prompt
    assert "observed_change" not in user_prompt
    assert '"description"' not in user_prompt
    assert "never arrays" in user_prompt
    assert "Do not write any digits" in user_prompt
    assert "Never" in system_prompt
    assert "never return an array" in system_prompt
    assert 'Never use "예측" except' in system_prompt
    raw = json.dumps(_v4_fields().model_dump(), ensure_ascii=False)
    assert parse_v4_llm_fields(raw) == _v4_fields()
    assert parse_v4_llm_fields(json.dumps({**_v4_fields().model_dump(), "extra": "x"})) is None


def test_v4_context_and_evidence_refs_are_deterministic():
    inputs = _v4_inputs()
    content = assemble_v4_report_content(inputs, _v4_fields())

    assert content is not None
    payload = build_v4_stored_payload(inputs, content)
    candidate_id = inputs.context_candidates[0].id

    assert payload.evidence_refs == ["metric:123", f"candidate:{candidate_id}"]
    assert payload.context_candidate_ids == [candidate_id]
    assert "두 공개 출처" in payload.content.context_summary
    assert "63.0%" in payload.content.observed_change
    assert "+8.0퍼센트포인트" in payload.content.observed_change
    assert "+11.0퍼센트포인트" in payload.content.observed_change
    assert run_v4_safety_and_semantic_checks(payload, inputs, _v4_fields()).passed


def test_v4_without_verified_context_uses_json_null_and_metric_ref_only():
    inputs = _v4_inputs(with_context=False)
    content = assemble_v4_report_content(inputs, _v4_fields())

    assert content is not None
    payload = build_v4_stored_payload(inputs, content)

    assert payload.content.context_summary is None
    assert payload.context_candidate_ids == []
    assert payload.evidence_refs == ["metric:123"]
    assert run_v4_safety_and_semantic_checks(payload, inputs, _v4_fields()).passed


@pytest.mark.parametrize(
    ("mutation", "expected_rule"),
    [
        ({"evidence_refs": ["metric:999"]}, "evidence_ref_mismatch"),
        ({"context_candidate_ids": []}, "candidate_id_mismatch"),
    ],
)
def test_v4_rejects_unknown_or_mismatched_evidence(mutation, expected_rule):
    inputs = _v4_inputs()
    content = assemble_v4_report_content(inputs, _v4_fields())
    payload = build_v4_stored_payload(inputs, content).model_copy(update=mutation)

    result = run_v4_safety_and_semantic_checks(payload, inputs, _v4_fields())

    assert result.passed is False
    assert result.rule == expected_rule


def test_v4_rejects_metric_or_context_text_that_differs_from_inputs():
    inputs = _v4_inputs()
    content = assemble_v4_report_content(inputs, _v4_fields())
    payload = build_v4_stored_payload(inputs, content)

    metric_payload = payload.model_copy(
        update={
            "content": payload.content.model_copy(
                update={
                    "observed_change": payload.content.observed_change.replace("63.0%", "73.0%")
                }
            )
        }
    )
    context_payload = payload.model_copy(
        update={
            "content": payload.content.model_copy(
                update={"context_summary": "다른 공개 정보가 관계를 설명합니다."}
            )
        }
    )

    assert (
        run_v4_safety_and_semantic_checks(metric_payload, inputs, _v4_fields()).rule
        == "metric_content_mismatch"
    )
    assert run_v4_safety_and_semantic_checks(context_payload, inputs, _v4_fields()).passed is False


@pytest.mark.parametrize(
    "fields",
    [
        _v4_fields(what_to_check="https://invented.example 자료를 추가로 확인해야 합니다."),
        _v4_fields(what_to_check="2027년 9월 99일 자료를 추가로 확인해야 합니다."),
        _v4_fields(what_to_check="관찰값은 공개 정보 때문에 달라졌다고 확인해야 합니다."),
    ],
)
def test_v4_rejects_model_added_url_number_or_relationship(fields):
    inputs = _v4_inputs()
    content = assemble_v4_report_content(inputs, fields)
    payload = build_v4_stored_payload(inputs, content)

    assert run_v4_safety_and_semantic_checks(payload, inputs, fields).passed is False


def test_v4_unknown_caution_level_cannot_assemble():
    with pytest.raises(ValueError, match="Unknown confidence_level"):
        assemble_v4_report_content(
            _v4_inputs(confidence_level="unknown"),
            _v4_fields(),
        )


# --- ADR-048 v5 evidence-bounded narrative -----------------------------


def test_v5_prompt_and_parser_use_exact_six_field_contract():
    inputs = _v4_inputs(
        title="Will JD Vance win the US Presidential Election?",
        description="Tracks whether JD Vance wins the documented election.",
        resolution_rules=ResolutionRulesInput(
            condition_text="JD Vance is recorded as the winner in the official result.",
            deadline=datetime(2026, 12, 31, tzinfo=UTC),
            exclusions=["An unofficial projection does not satisfy the condition."],
            resolution_source="https://example.gov/elections/result",
            source_description_hash="description-hash",
            rules_hash="rules-hash",
            collected_at=datetime(2026, 7, 11, 7, 0, tzinfo=UTC),
        ),
    )
    system_prompt, user_prompt = build_v5_prompt(inputs)

    assert "exactly six fields" in system_prompt
    assert "JD Vance" in user_prompt
    assert "verified_context_candidates" in user_prompt
    assert '"display_value_percent":63.0' in user_prompt
    assert '"display_change_24h_percentage_points":8.0' in user_prompt
    assert '"condition_text":"JD Vance is recorded as the winner' in user_prompt
    assert '"resolution_source":"https://example.gov/elections/result"' in user_prompt
    assert '"input_completeness":"definition_complete"' in user_prompt
    raw = json.dumps(_v5_fields().model_dump(), ensure_ascii=False)
    assert parse_v5_llm_fields(raw) == _v5_fields()
    assert (
        parse_v5_llm_fields(
            json.dumps({**_v5_fields().model_dump(), "extra": "x"}, ensure_ascii=False)
        )
        is None
    )


@pytest.mark.parametrize("with_context", [False, True])
def test_v5_assembles_deterministic_boundaries_and_evidence_refs(with_context):
    inputs = _v4_inputs(
        with_context=with_context,
        title="Will JD Vance win the US Presidential Election?",
        description="Tracks whether JD Vance wins the documented election.",
    )
    fields = _v5_fields(with_context=with_context)
    content = assemble_v5_report_content(inputs, fields)
    payload = build_v5_stored_payload(inputs, content)

    assert payload.content.relationship_boundary
    assert payload.content.data_limitations
    assert payload.content.caution_note
    assert payload.evidence_refs[0] == "metric:123"
    assert len(payload.context_candidate_ids) == int(with_context)
    assert run_v5_safety_and_semantic_checks(payload, inputs, fields).passed


def test_v5_rejects_generic_or_duplicated_narrative():
    inputs = _v4_inputs(
        with_context=False,
        title="Will JD Vance win the US Presidential Election?",
        description="Tracks whether JD Vance wins the documented election.",
    )
    generic = _v5_fields(
        with_context=False,
        executive_summary=(
            "이 항목은 문서에 적힌 조건을 살펴보는 내용입니다. 공개 데이터와 이후 자료를 "
            "함께 확인하되 현실의 결과를 뜻하는 것으로 해석하지 않습니다. 저장된 근거의 "
            "범위를 벗어난 배경이나 결과는 이 요약에서 판단하지 않습니다."
        ),
        factors_to_check=[
            {
                "title": "문서 확인",
                "explanation": "정해진 문서 조건을 이후 공개 자료에서 확인합니다.",
            },
            {
                "title": "시각 확인",
                "explanation": "정해진 기준일 안의 공개 여부를 함께 확인합니다.",
            },
        ],
    )
    generic_content = assemble_v5_report_content(inputs, generic)
    generic_payload = build_v5_stored_payload(inputs, generic_content)

    assert (
        run_v5_safety_and_semantic_checks(generic_payload, inputs, generic).rule
        == "generic_summary"
    )

    duplicate_text = (
        "JD Vance 관련 공식 문서와 선거 조건의 후속 갱신 내용을 차례로 확인할 필요가 있습니다."
    )
    duplicated = _v5_fields(
        with_context=False,
        factors_to_check=[
            {"title": "공식 문서", "explanation": duplicate_text},
            {
                "title": "판정 조건",
                "explanation": "JD Vance 선거 판정 조건을 공식 기록에서 확인합니다.",
            },
        ],
        signals_to_watch=[
            {"title": "공식 발표", "explanation": duplicate_text},
            {
                "title": "데이터 갱신",
                "explanation": "JD Vance 관련 공개 데이터의 갱신을 확인합니다.",
            },
        ],
    )
    duplicated_content = assemble_v5_report_content(inputs, duplicated)
    duplicated_payload = build_v5_stored_payload(inputs, duplicated_content)
    assert (
        run_v5_safety_and_semantic_checks(duplicated_payload, inputs, duplicated).rule
        == "duplicate_narrative_fields"
    )


def test_v5_rejects_evidence_synthesis_without_verified_candidate():
    inputs = _v4_inputs(
        with_context=False,
        title="Will JD Vance win the US Presidential Election?",
        description="Tracks whether JD Vance wins the documented election.",
    )
    fields = _v5_fields(with_context=True)
    content = assemble_v5_report_content(inputs, fields)
    payload = build_v5_stored_payload(inputs, content)

    assert (
        run_v5_safety_and_semantic_checks(payload, inputs, fields).rule
        == "evidence_synthesis_presence_mismatch"
    )


def test_v5_rejects_unsupported_numbers_and_nonconditional_scenarios():
    inputs = _v4_inputs(with_context=False)
    fields = _v5_fields(
        with_context=False,
        current_data_interpretation=(
            "저장된 현재 값은 99%이며 최근 비교 구간의 참여자 데이터와 함께 읽습니다. "
            "이 값만으로 현실의 결과를 판단할 수 없습니다."
        ),
    )
    content = assemble_v5_report_content(inputs, fields)
    payload = build_v5_stored_payload(inputs, content)

    assert run_v5_safety_and_semantic_checks(payload, inputs, fields).rule == "unsupported_number"
    invalid = fields.model_dump()
    invalid["conditional_scenarios"][0]["narrative"] = (
        "JD Vance 관련 공식 문서와 판정 조건을 순서대로 확인합니다."
    )
    assert parse_v5_llm_fields(json.dumps(invalid, ensure_ascii=False)) is None


def test_v5_number_validation_handles_missing_change_window():
    inputs = _v4_inputs(
        with_context=False,
        change_7d=None,
        title="Will JD Vance win the US Presidential Election?",
        description="Tracks whether JD Vance wins the documented election.",
    )
    fields = _v5_fields(with_context=False)
    content = assemble_v5_report_content(inputs, fields)
    payload = build_v5_stored_payload(inputs, content)

    assert run_v5_safety_and_semantic_checks(payload, inputs, fields).passed


def test_v5_missing_definition_requires_one_limitation_scenario():
    inputs = _v4_inputs(
        with_context=False,
        resolution_rules=None,
        title="이번 회기 AI 감독 법안 통과",
    )
    one_scenario = [
        {
            "title": "판정 정의 부족",
            "narrative": (
                "만약 현재 제공된 자료만 사용한다면 세부 판정 조건이 없어 "
                "구체적인 절차 경로를 구분할 수 없습니다."
            ),
        }
    ]
    fields = _v5_fields(
        with_context=False,
        executive_summary=(
            "이번 회기 AI 감독 법안 통과는 저장된 질문과 공개 데이터 값만으로 살펴보는 "
            "이슈입니다. 세부 판정 정의가 없어 현실의 결과를 뜻하지 않습니다."
        ),
        conditional_scenarios=one_scenario,
    )
    content = assemble_v5_report_content(inputs, fields)
    payload = build_v5_stored_payload(inputs, content)

    assert determine_input_completeness(inputs) == "definition_missing_no_context"
    assert run_v5_safety_and_semantic_checks(payload, inputs, fields).passed

    too_many = _v5_fields(
        with_context=False,
        executive_summary=fields.executive_summary,
    )
    too_many_content = assemble_v5_report_content(inputs, too_many)
    too_many_payload = build_v5_stored_payload(inputs, too_many_content)
    result = run_v5_safety_and_semantic_checks(too_many_payload, inputs, too_many)
    assert result.rule == "scenario_count_evidence_mismatch"


def test_v5_completeness_levels_are_deterministic():
    complete = _v4_inputs()
    partial = _v4_inputs(
        resolution_rules=complete.resolution_rules.model_copy(update={"deadline": None})
    )
    missing_with_context = _v4_inputs(resolution_rules=None, with_context=True)
    missing_without_context = _v4_inputs(resolution_rules=None, with_context=False)

    assert determine_input_completeness(complete) == "definition_complete"
    assert determine_input_completeness(partial) == "definition_partial"
    assert determine_input_completeness(missing_with_context) == "definition_missing_with_context"
    assert determine_input_completeness(missing_without_context) == "definition_missing_no_context"


@pytest.mark.parametrize(
    "executive_summary",
    [
            (
                "JD Vance 관련 선거 문서 조건을 살펴보는 이슈입니다. 공개 데이터 값은 "
                "현실의 결과를 뜻하지 않으며 저장된 근거 범위에서만 읽습니다. 세부 내용은 "
                "입력에 포함된 문서 조건을 벗어나지 않습니다."
            ),
        (
            "Will  JD Vance win the US Presidential Election? 질문의 문서 조건을 살펴봅니다. "
            "공개 데이터 값은 현실의 결과를 뜻하지 않습니다."
        ),
        (
            "Will JD Vance win the US Presidential Election? 질문과 "
            "Will JD Vance win the US Presidential Election? 질문의 문서 조건을 함께 살펴봅니다. "
            "공개 데이터 값은 현실의 결과를 뜻하지 않습니다."
        ),
    ],
)
def test_v5_requires_exact_market_title_once(executive_summary):
    inputs = _v4_inputs(with_context=False)
    fields = _v5_fields(with_context=False, executive_summary=executive_summary)
    content = assemble_v5_report_content(inputs, fields)
    payload = build_v5_stored_payload(inputs, content)

    result = run_v5_safety_and_semantic_checks(payload, inputs, fields)

    assert result.rule == "exact_title_occurrence_mismatch"
    assert result.field == "executive_summary"
