"""TASK-049: ADR-033 v3 build_prompt(), the strict LLM-field parse,
deterministic field assembly, the banned-phrase/pattern safety filter, and
the cross-field semantic checks. Pure logic - no database needed; the
regeneration/storage orchestration lives in test_ai_report_batch.py.
"""

import json
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
    assemble_report_content,
    build_caution_note,
    build_data_limitations,
    build_external_context,
    build_openai_client,
    build_possible_drivers,
    build_prompt,
    build_what_to_check,
    parse_llm_fields,
    run_safety_filter,
    run_semantic_checks,
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
        "24시간 전보다 8.2퍼센트포인트 높게 관찰되었습니다."
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


# --- build_prompt -------------------------------------------------------


def test_build_prompt_returns_fixed_system_prompt_verbatim():
    system_prompt, _ = build_prompt(_inputs())
    assert system_prompt == SYSTEM_PROMPT


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
    assert build_possible_drivers(_reviewed_candidate_inputs()) == POSSIBLE_DRIVERS_WITH_CANDIDATE


def test_possible_drivers_never_embeds_actual_title_or_date_text():
    """Weak-inference rule: possible_drivers is a generic comparison
    statement, never a restatement that could be mistaken for an
    explanation - the actual title/date lives in external_context only."""
    text = build_possible_drivers(_reviewed_candidate_inputs())
    assert "Kraken" not in text
    assert "2026-02-18" not in text


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
    content = assemble_report_content(
        _inputs(confidence_level="not_a_real_level"), _llm_fields()
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
    tampered = content.model_copy(update={"possible_drivers": POSSIBLE_DRIVERS_WITH_CANDIDATE})
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
    assert _resolve_ai_model("openrouter", raw_model="~openai/gpt-latest") == (
        "~openai/gpt-latest"
    )


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
    assert stub.completions.kwargs["extra_headers"] == {
        "X-OpenRouter-Title": "Outlook Signals"
    }
