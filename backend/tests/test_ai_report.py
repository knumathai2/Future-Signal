"""TASK-015: build_prompt(), the strict JSON-schema parse, and the
banned-phrase/pattern safety filter. Pure logic - no database needed; the
regeneration/storage orchestration lives in test_ai_report_batch.py.
"""

import httpx
import openai
import pytest

from app.core.ai_report import (
    SYSTEM_PROMPT,
    LLMCallError,
    OpenAIReportClient,
    ReportPromptInputs,
    build_openai_client,
    build_prompt,
    parse_report_content,
    run_safety_filter,
)
from app.core.config import (
    OPENROUTER_BASE_URL,
    _resolve_ai_base_url,
    _resolve_ai_model,
    _resolve_ai_provider,
)
from app.schemas.issues import ReportContent

VALID_CONTENT = {
    "issue_summary": "This market tracks whether the issue resolves Yes by the deadline.",
    "movement_explanation": (
        "Over the past 7 days, the reflected expectation rose by 11 percentage points."
    ),
    "key_change_context": (
        "A related event candidate occurred alongside this period; offered as context, "
        "not a cause."
    ),
    "uncertainty_summary": (
        "Trading activity has been moderate; interpret short-term swings with some caution."
    ),
    "neutral_conclusion": "Public expectation on this issue has shifted upward over the past week.",
}


def _inputs(**overrides) -> ReportPromptInputs:
    base = dict(
        title="Will the test issue resolve Yes?",
        description="A seeded test issue.",
        category="technology",
        current_value=0.63,
        change_24h=0.08,
        change_7d=0.11,
        confidence_level="sufficient",
        inflection_point_summary="A +8.0pp expectation shift was detected in the 24h window.",
        related_event_or_none="A related context event (2026-07-07): context only, not a cause.",
    )
    base.update(overrides)
    return ReportPromptInputs(**base)


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
    assert '"issue_summary": "..."' in user_prompt
    assert '"neutral_conclusion": "..."' in user_prompt


def test_build_prompt_uses_none_placeholder_when_no_inflection_or_event():
    _, user_prompt = build_prompt(
        _inputs(inflection_point_summary=None, related_event_or_none=None)
    )
    assert "Recent inflection point (if any): None" in user_prompt
    assert "Related event candidate (if any): None" in user_prompt


def test_build_prompt_reports_missing_change_windows_as_not_available_never_zero():
    _, user_prompt = build_prompt(_inputs(change_24h=None, change_7d=None))
    assert "not available" in user_prompt
    assert "0.0pp" not in user_prompt


# --- parse_report_content -----------------------------------------------


def test_parse_valid_json_returns_report_content():
    import json

    content = parse_report_content(json.dumps(VALID_CONTENT))
    assert isinstance(content, ReportContent)
    assert content.issue_summary == VALID_CONTENT["issue_summary"]


def test_parse_malformed_json_returns_none():
    assert parse_report_content("{not valid json") is None


def test_parse_non_object_json_returns_none():
    assert parse_report_content("[1, 2, 3]") is None


def test_parse_missing_field_returns_none_not_partial():
    incomplete = dict(VALID_CONTENT)
    del incomplete["neutral_conclusion"]
    import json

    assert parse_report_content(json.dumps(incomplete)) is None


def test_parse_extra_field_returns_none():
    extended = dict(VALID_CONTENT, extra_field="free-form analysis the model added")
    import json

    assert parse_report_content(json.dumps(extended)) is None


# --- run_safety_filter ----------------------------------------------------


def test_clean_content_passes_filter():
    content = ReportContent(**VALID_CONTENT)
    result = run_safety_filter(content)
    assert result.passed is True


@pytest.mark.parametrize(
    "field,text",
    [
        ("issue_summary", "You should buy into this issue now."),
        ("movement_explanation", "This looks like a good bet for traders."),
        ("key_change_context", "Consider a long position given the trend."),
        ("uncertainty_summary", "This is a guaranteed win rate scenario."),
        ("neutral_conclusion", "We recommend following this expert trader."),
    ],
)
def test_banned_phrase_is_rejected(field, text):
    content = ReportContent(**dict(VALID_CONTENT, **{field: text}))
    result = run_safety_filter(content)
    assert result.passed is False
    assert result.field == field


@pytest.mark.parametrize(
    "text",
    [
        "This will happen by the end of the month.",
        "You should check this issue again soon.",
        "The shift occurred because of a related event.",
        "Prices moved due to a related event candidate.",
        "The change was caused by a related event candidate.",
    ],
)
def test_banned_pattern_is_rejected(text):
    content = ReportContent(**dict(VALID_CONTENT, neutral_conclusion=text))
    result = run_safety_filter(content)
    assert result.passed is False
    assert result.rule.startswith("banned_pattern:")


def test_substring_false_positive_is_not_rejected():
    # "belong" contains "long", "shortly" contains "short" - word-boundary
    # matching must not reject these.
    content = ReportContent(
        **dict(
            VALID_CONTENT,
            neutral_conclusion=(
                "This issue does not belong to a single category and may update shortly."
            ),
        )
    )
    result = run_safety_filter(content)
    assert result.passed is True


def test_technical_design_10_3_reference_example_parses_and_passes_filter():
    """Technical Design §10.3's own reference output must round-trip clean -
    this is the DoD's "exact tone and format" acceptance check."""
    import json

    example = {
        "issue_summary": (
            "This market tracks whether [event] will be resolved as 'Yes' by [date], "
            "based on public trading activity on Polymarket."
        ),
        "movement_explanation": (
            "Over the past 7 days, the expectation reflected in this market rose by 11 "
            "percentage points, with the largest single shift occurring around [date]."
        ),
        "key_change_context": (
            "A related event candidate around this time: [event]. This is offered as "
            "context, not as a confirmed cause."
        ),
        "uncertainty_summary": (
            "Trading activity on this market has been moderate over this period; "
            "interpret short-term swings with some caution."
        ),
        "neutral_conclusion": (
            "Public expectation on this issue has shifted upward over the past week, "
            "though the underlying data reflects market activity rather than a factual "
            "forecast."
        ),
    }

    content = parse_report_content(json.dumps(example))
    assert content is not None
    assert run_safety_filter(content).passed is True


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
