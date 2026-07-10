"""AI report generation (TASK-049): ADR-033 v3 fixed eight-field content,
LLM call, strict schema parse, deterministic field assembly, and the
banned-phrase/pattern/semantic safety validation that runs before storage.

Scope note: this module produces a `ReportContent` (or a documented failure)
for exactly one market. It does not decide *which* markets to regenerate or
touch `ai_reports`/`data_collection_logs` directly - that orchestration
(regeneration eligibility, top-10 cap, storage, audit logging) is
`app/core/ai_report_batch.py`. Keeping the boundary here means the prompt/
parse/assemble/filter logic can be unit-tested with a fake `LLMClient` and no
database at all.

ADR-033 design note: only `issue_overview`, `current_data_reading`, and
`possible_outlook` are LLM-authored prose, constrained by the fixed prompt
below. `possible_drivers`, `external_context`, `what_to_check`,
`data_limitations`, and `caution_note` are assembled deterministically from
structured inputs in this module, never from LLM free text - ADR-033 requires
an exact deterministic caution literal, a non-inventive candidate index for
`possible_drivers`, and a verbatim pass-through (no added inference) for
`external_context`. Keeping these five fields out of the LLM prompt entirely
also means the model is never shown the related-event candidate and cannot
weave it into `possible_outlook`/`current_data_reading` with causal framing.

`ReportContent` here is this module's own structural validation copy of the
ADR-033 contract (`backend/API_CONTRACT.md`), not `app/schemas/issues.py`.
Backend/TASK-050 owns the public API Pydantic schema; this keeps the two
tasks' edits from colliding while both target the same frozen contract.

AI provider: OpenAI-compatible chat completions, with OpenRouter selected when
configured, per human-approved ADRs in memory/decisions.md.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.snapshot_metrics import (
    CAUTION_HIGH_VOLATILITY_THRESHOLD,
    CAUTION_LOW_ACTIVITY_LIQUIDITY_THRESHOLD,
    CAUTION_LOW_ACTIVITY_VOLUME_THRESHOLD,
)

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v3"

# --------------------------------------------------------------------------
# 10.1 System prompt (fixed, never modified per-request)
#
# Only asks the model for the three narrative fields that legitimately vary
# per issue. The related-event candidate is deliberately never shown here -
# see module docstring.
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are generating a concise, neutral public-data reading for a public
issue-monitoring dashboard. Write in clear Korean for non-specialist readers.
You are explaining the market question and the public data context, not
predicting real-world outcomes and not giving advice of any kind.

Rules you must always follow:
- Describe the issue and its documented condition in plain language before
  mentioning the data reading.
- Frame every value as a reading of public prediction-market participant
  data, never as a probability or forecast of a real-world outcome.
- Never label anything as best, worst, good, bad, desirable, or undesirable.
- Never state or imply that a real-world outcome will or will not happen.
- Never use: bet, buy, sell, trade, position, long, short, profit, win rate,
  recommend, guaranteed, best pick, follow, copy, opportunity - or their
  Korean equivalents (베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당,
  추천, 보장, 확정, 따라하기, 고수, 전문 트레이더, 고수익, 기회).
- Never suggest any action the reader should take.
- Never use causal connectors such as "because", "due to", or "caused by"
  (or 때문에, ~로 인해, 원인) to link any event to the observed movement.
- For the possible-outlook field, describe only conditional continuation,
  expansion, or moderation of the public-data reading itself in later
  readings - never assert a real-world result, a probability of one, or a
  certain future direction (avoid constructions such as ~할 것이다, 가능성이
  높다/낮다, 전망, 예측 when describing a real-world result).
- After trimming whitespace, meet the ADR-033 Unicode character bounds for
  every field: issue_overview 30-600 characters, current_data_reading 50-700
  characters, and possible_outlook 60-700 characters.
- Keep every field to 1-5 concise sentences."""

# --------------------------------------------------------------------------
# 10.2 User/task prompt template (fixed - the only variation between calls is
# filling these named slots, never additional free text)
# --------------------------------------------------------------------------
USER_PROMPT_TEMPLATE = """\
Market title: {title}
Market description: {description}
Category: {category}
Tracked outcome label: {outcome_label}
Documented end date: {end_date}
Current expectation value: {current_value}
24h change: {change_24h}
7d change: {change_7d}
Data reliability/caution level: {confidence_level}
Recent inflection point (if any): {inflection_point_summary}

Produce a JSON object in Korean with exactly these fields:
{{
  "issue_overview": "...",
  "current_data_reading": "...",
  "possible_outlook": "..."
}}"""


@dataclass
class ReportPromptInputs:
    """Structured, already-computed inputs only - never raw free text from a
    user or an unvetted source. `related_event_*` fields come only from the
    PM/Data-approved curated `related_events` path (Service Design §8) and are
    used solely by the deterministic field builders below, never inserted
    into the LLM prompt."""

    title: str
    description: str
    category: str
    outcome_label: str | None
    end_date: datetime | None
    current_value: float
    change_24h: float | None
    change_7d: float | None
    confidence_level: str
    inflection_point_summary: str | None
    volume_24h: float | None
    liquidity: float | None
    related_event_title: str | None
    related_event_date: datetime | None
    related_event_note: str | None


def _format_pp(change: float | None) -> str:
    """`change_24h`/`change_7d` are raw 0-1 deltas (Technical Design §7) -
    render as percentage points, or an explicit not-available string rather
    than fabricating 0 (no-fabrication rule, AGENTS.md)."""
    if change is None:
        return "not available (insufficient history)"
    return f"{change * 100:+.1f}pp"


def _format_end_date(end_date: datetime | None) -> str:
    if end_date is None:
        return "No documented end date"
    return end_date.date().isoformat()


def build_prompt(inputs: ReportPromptInputs) -> tuple[str, str]:
    """Returns `(system_prompt, user_prompt)`. `SYSTEM_PROMPT` is returned
    verbatim; `user_prompt` is `USER_PROMPT_TEMPLATE` with only the named
    slots filled from `inputs` - no other text is ever inserted."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=inputs.title,
        description=inputs.description,
        category=inputs.category,
        outcome_label=inputs.outcome_label or "Not documented",
        end_date=_format_end_date(inputs.end_date),
        current_value=f"{inputs.current_value * 100:.1f}%",
        change_24h=_format_pp(inputs.change_24h),
        change_7d=_format_pp(inputs.change_7d),
        confidence_level=inputs.confidence_level,
        inflection_point_summary=inputs.inflection_point_summary or "None",
    )
    return SYSTEM_PROMPT, user_prompt


# --------------------------------------------------------------------------
# LLM client abstraction - callers pick the provider explicitly; nothing in
# this module calls a network API on its own.
# --------------------------------------------------------------------------


class LLMCallError(Exception):
    """Raised by any `LLMClient.complete()` on timeout/API failure so callers
    have one exception type to retry against, regardless of provider."""


class LLMClient(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Returns the raw model text output (expected to be a JSON string).
        Must raise `LLMCallError` on timeout/API failure."""
        ...


class OpenAICompatibleReportClient:
    """`LLMClient` backed by OpenAI-compatible Chat Completions.

    The concrete provider is selected by the caller through the SDK client
    configuration, for example OpenRouter via `base_url`. Constructing this
    class is the explicit, caller-initiated point where a paid external API
    becomes reachable; nothing elsewhere in this module does so implicitly.
    """

    def __init__(
        self,
        client: OpenAI,
        model: str,
        *,
        provider_name: str = "OpenAI",
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._provider_name = provider_name
        self._extra_headers = extra_headers or {}

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            kwargs = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
                "timeout": 20,
            }
            if self._extra_headers:
                kwargs["extra_headers"] = self._extra_headers
            response = self._client.chat.completions.create(**kwargs)
        except OpenAIError as exc:
            # standards.md: never log full LLM prompts/responses.
            raise LLMCallError(
                f"{self._provider_name} call failed: {type(exc).__name__}"
            ) from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMCallError(f"Empty response from {self._provider_name}.")
        return content


OpenAIReportClient = OpenAICompatibleReportClient


def build_openai_client(
    api_key: str,
    model: str,
    *,
    base_url: str | None = None,
    provider_name: str = "OpenAI",
    extra_headers: dict[str, str] | None = None,
) -> OpenAICompatibleReportClient:
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAICompatibleReportClient(
        OpenAI(**kwargs),
        model,
        provider_name=provider_name,
        extra_headers=extra_headers,
    )


# --------------------------------------------------------------------------
# LLM output schema (the three model-authored fields only) and the frozen
# ADR-033 eight-field content schema (structural validation only - semantic
# safety runs separately, below).
# --------------------------------------------------------------------------


class LLMReportFields(BaseModel):
    """Strict parse target for the raw LLM JSON response. `extra="forbid"` -
    a response with an extra field fails validation here rather than being
    silently trimmed (Technical Design §10.6)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_overview: str
    current_data_reading: str
    possible_outlook: str


_SENTENCE_TERMINATOR_PATTERN = re.compile(r"[.!?]+(?=\s|$)")


def _sentence_count(value: str) -> int:
    """Count prose sentences consistently for the ADR-033 1-5 limit."""
    matches = _SENTENCE_TERMINATOR_PATTERN.findall(value.strip())
    return len(matches) or 1


class ReportContent(BaseModel):
    """Frozen ADR-033 v3 report content - exactly eight fields, `external_context`
    the only nullable value. This module's own validation copy of the contract
    in `backend/API_CONTRACT.md`; Backend/TASK-050 owns the public API schema
    copy. Length bounds are trimmed Unicode code points (ADR-033)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_overview: str = Field(min_length=30, max_length=600)
    current_data_reading: str = Field(min_length=50, max_length=700)
    possible_outlook: str = Field(min_length=60, max_length=700)
    possible_drivers: str = Field(min_length=80, max_length=700)
    external_context: str | None = Field(default=..., min_length=40, max_length=700)
    what_to_check: str = Field(min_length=30, max_length=600)
    data_limitations: str = Field(min_length=80, max_length=700)
    caution_note: str = Field(min_length=120, max_length=700)

    @field_validator("*")
    @classmethod
    def limit_sentence_count(cls, value: str | None) -> str | None:
        """ADR-033 limits every non-null report field to five sentences."""
        if value is not None and _sentence_count(value) > 5:
            raise ValueError("Report fields must contain at most five sentences.")
        return value


def parse_llm_fields(raw_text: str) -> LLMReportFields | None:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return LLMReportFields.model_validate(payload)
    except ValidationError:
        return None


# --------------------------------------------------------------------------
# Deterministic field builders (ADR-033: possible_drivers, external_context,
# what_to_check, data_limitations, and caution_note are never LLM free text).
# --------------------------------------------------------------------------

# Fixed Korean statements reused from the ADR-033/API_CONTRACT.md approved
# example and the approved no-candidate literal. The candidate-present value is
# a format template because ADR-033 requires the reviewed title and recorded
# date to remain visible in the deterministic comparison index.
POSSIBLE_DRIVERS_WITH_CANDIDATE = (
    "수동 검토를 마친 맥락 후보 「{title}」의 기록 날짜 {date}는 관찰된 움직임과 "
    "함께 비교할 수 있습니다. 해당 시점은 비교를 위해 제공되며, 현재 데이터는 이 "
    "맥락 후보와 움직임 사이의 관계를 입증하지 않습니다."
)
POSSIBLE_DRIVERS_NO_CANDIDATE = (
    "이 움직임과 함께 비교할 수 있도록 수동 검토를 마친 맥락 후보가 없습니다. "
    "현재 데이터는 관찰된 움직임만 보여 주며, 추가 맥락은 다른 자료를 통해 "
    "독립적으로 확인해야 합니다."
)

_DATA_LIMITATIONS_BASELINE = (
    "이 읽기는 활동량, 유동성, 24시간 변화 폭, 24시간 및 7일 이력 범위의 영향을 받습니다."
)
_DATA_LIMITATIONS_MISSING_HISTORY = (
    "필요한 24시간 또는 7일 비교 지점 중 하나 이상이 없어 방향, 크기, "
    "연속성을 판단할 수 없습니다."
)
_DATA_LIMITATIONS_LOW_ACTIVITY = (
    "24시간 활동량 또는 유동성이 없거나 설정된 하한보다 낮아 관찰된 변화가 "
    "제한된 활동이나 깊이에 민감할 수 있습니다."
)
_DATA_LIMITATIONS_HIGH_VOLATILITY = (
    "24시간 기대값 변화의 절대 폭이 설정된 큰 움직임 기준을 넘어 단기 "
    "움직임을 안정된 흐름으로 해석하기 어렵습니다."
)
_DATA_LIMITATIONS_REPRESENTATIVENESS = (
    "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다."
)

# Exact deterministic Korean literal per `confidence_level` (ADR-033 caution
# matrix). Copied verbatim from `backend/API_CONTRACT.md` - never paraphrased.
CAUTION_NOTE_BY_LEVEL: dict[str, str] = {
    "sufficient": (
        "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, "
        "전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. "
        "24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 "
        "않으며 24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, 다른 자료를 "
        "통해 독립적으로 확인해야 합니다."
    ),
    "caution_low_activity": (
        "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, "
        "전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. "
        "24시간 활동량 또는 유동성이 없거나 설정된 하한보다 낮아 관찰된 변화가 "
        "제한된 활동이나 깊이에 민감할 수 있으므로, 다른 자료를 통해 "
        "독립적으로 확인해야 합니다."
    ),
    "caution_high_volatility": (
        "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, "
        "전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. "
        "필요한 비교 지점과 활동 조건을 통과했지만 24시간 기대값 변화의 절대 "
        "폭이 15퍼센트포인트를 넘어 단기 움직임을 안정된 흐름으로 해석하기 "
        "어려우므로, 다른 자료를 통해 독립적으로 확인해야 합니다."
    ),
    "insufficient_data": (
        "이 내용은 제한된 공개 예측시장 참여자 데이터를 정리한 것이며, 전체 "
        "대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 필요한 "
        "24시간 또는 7일 비교 지점 중 하나 이상이 없어 요청 구간의 방향, "
        "크기, 연속성을 판단할 수 없으므로, 다른 자료를 통해 독립적으로 "
        "확인해야 합니다."
    ),
}


def _has_reviewed_candidate(inputs: ReportPromptInputs) -> bool:
    """A candidate exists only via the PM/Data-approved curated
    `related_events` path (Service Design §8) - title presence is the signal
    that a row was found for this market."""
    return bool((inputs.related_event_title or "").strip())


def _format_related_event_date(event_date: datetime | None) -> str:
    """Format a reviewed candidate date without fabricating a missing value."""
    if event_date is None:
        return "기록 날짜가 제공되지 않았습니다"
    return event_date.date().isoformat()


def build_possible_drivers(inputs: ReportPromptInputs) -> str:
    """Build the deterministic candidate index required by ADR-033.

    A reviewed title and date are comparison context, not an explanation of
    the movement. Missing dates stay explicit rather than being fabricated.
    """
    if not _has_reviewed_candidate(inputs):
        return POSSIBLE_DRIVERS_NO_CANDIDATE
    return POSSIBLE_DRIVERS_WITH_CANDIDATE.format(
        title=(inputs.related_event_title or "").strip(),
        date=_format_related_event_date(inputs.related_event_date),
    )


def build_external_context(inputs: ReportPromptInputs) -> str | None:
    """Verbatim pass-through of the PM/Data-reviewed note only - no new
    inference or provenance claim is added (ADR-033 Option A). `null` when no
    reviewed note exists for this market."""
    if not inputs.related_event_note:
        return None
    return inputs.related_event_note


def build_what_to_check(inputs: ReportPromptInputs) -> str:
    """Deterministic verification checklist from stored/curated fields and
    structured missing-input flags - never an instruction to act on an
    outcome (ADR-033 missing-value behavior: fixed check of published issue
    wording, recorded dates, later public-data updates, and timestamp)."""
    end_date_clause = (
        f"{_format_end_date(inputs.end_date)}로 기록된 기준일"
        if inputs.end_date is not None
        else "문서에 기록된 기준일"
    )
    context_clause = (
        ", 수동 검토를 마친 맥락 후보의 기록 날짜"
        if _has_reviewed_candidate(inputs)
        else ""
    )
    return (
        f"이슈에 적힌 조건과 {end_date_clause}{context_clause}, "
        "그리고 이후 공개되는 데이터 갱신 내용을 추가로 확인해야 합니다."
    )


def build_data_limitations(inputs: ReportPromptInputs) -> str:
    """Independently detects each raw limitation from structured inputs
    rather than relying on the collapsed `confidence_level` enum alone
    (ADR-033: "one enum can hide another raw limitation") - always includes
    the representativeness disclaimer."""
    missing_history = inputs.change_24h is None or inputs.change_7d is None
    low_activity = (
        inputs.volume_24h is None
        or inputs.volume_24h < CAUTION_LOW_ACTIVITY_VOLUME_THRESHOLD
        or inputs.liquidity is None
        or inputs.liquidity < CAUTION_LOW_ACTIVITY_LIQUIDITY_THRESHOLD
    )
    high_volatility = (
        inputs.change_24h is not None
        and abs(inputs.change_24h) > CAUTION_HIGH_VOLATILITY_THRESHOLD
    )

    sentences = [
        _DATA_LIMITATIONS_MISSING_HISTORY if missing_history else _DATA_LIMITATIONS_BASELINE
    ]
    if low_activity:
        sentences.append(_DATA_LIMITATIONS_LOW_ACTIVITY)
    if high_volatility:
        sentences.append(_DATA_LIMITATIONS_HIGH_VOLATILITY)
    sentences.append(_DATA_LIMITATIONS_REPRESENTATIVENESS)
    return " ".join(sentences)


def build_caution_note(confidence_level: str) -> str:
    """Exact deterministic Korean literal selected from `confidence_level`
    (ADR-033 caution matrix) - never LLM-authored or paraphrased."""
    literal = CAUTION_NOTE_BY_LEVEL.get(confidence_level)
    if literal is None:
        raise ValueError(f"Unknown confidence_level: {confidence_level!r}")
    return literal


def assemble_report_content(
    inputs: ReportPromptInputs, llm_fields: LLMReportFields
) -> ReportContent | None:
    """Merges the three LLM-authored fields with the five deterministically
    built fields into the frozen ADR-033 shape. Returns `None` (never a
    partially-valid object) if any field violates the structural bounds or
    `confidence_level` is unrecognized."""
    try:
        return ReportContent(
            issue_overview=llm_fields.issue_overview,
            current_data_reading=llm_fields.current_data_reading,
            possible_outlook=llm_fields.possible_outlook,
            possible_drivers=build_possible_drivers(inputs),
            external_context=build_external_context(inputs),
            what_to_check=build_what_to_check(inputs),
            data_limitations=build_data_limitations(inputs),
            caution_note=build_caution_note(inputs.confidence_level),
        )
    except (ValidationError, ValueError):
        return None


# --------------------------------------------------------------------------
# 10.4 Safety filter - runs after every generation, before storage.
# --------------------------------------------------------------------------

# Union of standards.md's Content Safety Lint prohibited list (English +
# Korean v3 additions), UX Design §5.3, memory/glossary.md's wording policy,
# and the system prompt's own never-use list. Single words are matched on
# word boundaries so e.g. "long" doesn't also reject "belong"; multi-word
# phrases match as a unit. Korean terms use plain substring matching (Korean
# has no "long-term"/"trade-off" style hyphen-compound ambiguity here).
BANNED_PHRASES: tuple[str, ...] = (
    "bet",
    "buy",
    "sell",
    "trade",
    "position",
    "long",
    "short",
    "profit",
    "win rate",
    "odds",
    "copy trader",
    "follow this user",
    "expert trader",
    "best pick",
    "recommended outcome",
    "high-return opportunity",
    "high-return",
    "guaranteed prediction",
    "guaranteed",
    "signal to act",
    "recommendation",
    "recommend",
    "follow",
    "copy",
    "opportunity",
)

# Korean v3 hard-block additions (ADR-033 / standards.md / memory/glossary.md).
KOREAN_BANNED_SUBSTRINGS: tuple[str, ...] = (
    "베팅",
    "매수",
    "매도",
    "포지션",
    "롱",
    "숏",
    "수익",
    "승률",
    "배당",
    "추천",
    "보장",
    "확정",
    "따라하기",
    "고수",
    "전문 트레이더",
    "고수익",
    "기회",
)

# Structural rules (standards.md Content Safety Lint + Technical Design
# §10.4 + ADR-033): causal language, future-outcome/certainty language, and
# action-suggesting phrasing, independent of the single-word list above.
# Applied uniformly across all fields - a stricter superset of ADR-033's
# field-specific framing is still compliant ("tightens, never weakens").
BANNED_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bwill (happen|occur|rise|fall|reverse|continue|increase|decrease)\b",
        r"\byou should\b",
        r"\bbecause\b",
        r"\bdue to\b",
        r"\bcaused by\b",
        r"\bled to\b",
        r"\bresulted in\b",
        r"\bexplains? the movement\b",
        r"\b(drove|triggered|produced) the movement\b",
        r"\bmain factor\b",
        r"\bprimary explanation\b",
        r"\b(preferred|favorable|adverse|expected) scenario\b",
    )
)

# Korean causal-connector and forecast/certainty patterns (ADR-033
# weak-inference and possible_outlook safety rules). Quoted here only to
# define the blocking rule (standards.md).
KOREAN_BANNED_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p)
    for p in (
        r"때문에",
        r"로\s*인해",
        r"주요\s*요인",
        # Allow the ADR-033-approved negative disclaimer, while still
        # rejecting positive causal claims such as "변화의 원인입니다".
        r"원인(?!으로\s*제시되지\s*않|이\s*아니|이\s*아님)",
        r"영향을\s*주었다",
        r"촉발했다",
        r"할\s*것이다",
        r"하게\s*된다",
        r"가능성이\s*높다",
        r"가능성이\s*낮다",
        r"상승이\s*이어진다",
        r"하락이\s*이어진다",
        r"전망",
        # Excludes the approved domain compound "예측시장" (prediction
        # market) used throughout every ADR-033 caution/limitation literal -
        # only bans "예측" (forecast) in every other context.
        r"예측(?!시장)",
    )
)

_PHRASE_PATTERNS: tuple[re.Pattern, ...] = tuple(
    # Custom boundary (not \b): \b treats "-" as a boundary character, which
    # would false-positive-reject entirely benign compounds like
    # "short-term"/"long-term"/"trade-off" (a hyphen-joined compound is not
    # the trading-position/action sense these words are banned for). Require
    # the match not be directly adjacent to another word char *or* a hyphen
    # on either side instead.
    re.compile(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", re.IGNORECASE)
    for phrase in BANNED_PHRASES
)

_KOREAN_PHRASE_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(re.escape(phrase)) for phrase in KOREAN_BANNED_SUBSTRINGS
)

REPORT_FIELDS: tuple[str, ...] = (
    "issue_overview",
    "current_data_reading",
    "possible_outlook",
    "possible_drivers",
    "external_context",
    "what_to_check",
    "data_limitations",
    "caution_note",
)


@dataclass
class SafetyFilterResult:
    passed: bool
    rule: str | None = None  # e.g. "banned_phrase:bet" or "banned_pattern:\\bbecause\\b"
    field: str | None = None


def run_safety_filter(content: ReportContent) -> SafetyFilterResult:
    """Checks every field individually (so a failure can report *which*
    field/rule tripped, per Technical Design §10.4's logging requirement)
    against the banned-phrase list, then the banned-pattern list, in English
    then Korean. `external_context` is skipped when `None` (nothing to
    check)."""
    for field in REPORT_FIELDS:
        text = getattr(content, field)
        if text is None:
            continue
        for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(passed=False, rule=f"banned_phrase:{phrase}", field=field)
        for phrase, pattern in zip(
            KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True
        ):
            if pattern.search(text):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_phrase:{phrase}", field=field
                )
        for pattern in BANNED_PATTERNS:
            if pattern.search(text):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_pattern:{pattern.pattern}", field=field
                )
        for pattern in KOREAN_BANNED_PATTERNS:
            if pattern.search(text):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_pattern:{pattern.pattern}", field=field
                )
    return SafetyFilterResult(passed=True)


# --------------------------------------------------------------------------
# ADR-033 semantic/structural cross-field checks - independent of the
# phrase/pattern scan above. These verify the deterministic fields actually
# match what the inputs require, as a defense-in-depth check on the
# `assemble_report_content` builders themselves.
# --------------------------------------------------------------------------

_CANDIDATE_QUALIFIER_TERMS: tuple[str, ...] = ("candidate", "후보", "맥락 메모")
_NOT_CAUSE_QUALIFIER_TERMS: tuple[str, ...] = (
    "not a cause",
    "not presented as a cause",
    "not the cause",
    "원인이 아니",
    "원인으로 제시되지 않",
    "인과관계를 밝히지",
)


def _external_context_has_required_qualifier(note: str) -> bool:
    """ADR-033: every `external_context` item must carry a candidate-not-cause
    qualifier. Heuristic substring check - defense in depth on top of the
    curated-data review process, not a replacement for it."""
    lowered = note.lower()
    has_candidate_term = any(term.lower() in lowered for term in _CANDIDATE_QUALIFIER_TERMS)
    has_not_cause_term = any(term.lower() in lowered for term in _NOT_CAUSE_QUALIFIER_TERMS)
    return has_candidate_term and has_not_cause_term


_PERCENT_VALUE_PATTERN = re.compile(
    r"(?<![\d.])([+-]?\d+(?:[.,]\d+)?)\s*(?:%|퍼센트)(?!포인트)",
    re.IGNORECASE,
)
_PERCENT_POINT_VALUE_PATTERN = re.compile(
    r"(?<![\d.])([+-]?\d+(?:[.,]\d+)?)\s*(?:퍼센트포인트|%p|pp)(?!\w)",
    re.IGNORECASE,
)


def _parse_numeric_tokens(pattern: re.Pattern[str], text: str) -> list[float]:
    """Parse localized metric tokens while tolerating comma decimals."""
    return [float(raw.replace(",", ".")) for raw in pattern.findall(text)]


def _approximately_matches(actual: float, expected: float) -> bool:
    """Allow the one-decimal rounding used by the prompt and UI copy."""
    return abs(actual - expected) <= 0.06


def _current_data_reading_matches_inputs(
    text: str, inputs: ReportPromptInputs
) -> bool:
    """Reject metric-bearing model prose that contradicts structured inputs.

    The model may omit a metric when it uses a neutral non-numeric sentence,
    but every percentage or percentage-point value it does state must match a
    current value or available 24h/7d change. This prevents unsupported values
    from reaching storage without forcing one exact Korean sentence shape.
    """
    percent_values = _parse_numeric_tokens(_PERCENT_VALUE_PATTERN, text)
    if any(
        not _approximately_matches(value, inputs.current_value * 100)
        for value in percent_values
    ):
        return False

    available_changes = [
        change * 100
        for change in (inputs.change_24h, inputs.change_7d)
        if change is not None
    ]
    point_values = _parse_numeric_tokens(_PERCENT_POINT_VALUE_PATTERN, text)
    if any(
        not any(_approximately_matches(value, expected) for expected in available_changes)
        for value in point_values
    ):
        return False

    if point_values and not available_changes:
        return False

    mentions_24h = "24시간" in text or "24h" in text.lower()
    mentions_7d = "7일" in text or "7d" in text.lower()
    if mentions_24h and inputs.change_24h is None:
        return False
    if mentions_7d and inputs.change_7d is None:
        return False
    return True


def _has_public_participant_data_scope(text: str) -> bool:
    """Require the report to identify the reading as scoped public data."""
    lowered = text.lower()
    korean_scope = "공개" in text and "데이터" in text and (
        "참여자" in text or "예측시장" in text
    )
    english_scope = "public" in lowered and "data" in lowered and (
        "participant" in lowered or "prediction market" in lowered
    )
    return korean_scope or english_scope


_CONDITIONAL_OUTLOOK_PATTERN = re.compile(
    r"(?:경우|다면|더라도|수\s*있|\bif\b|\bwhen\b|\bcould\b|\bmight\b|\bmay\b)",
    re.IGNORECASE,
)


def _possible_outlook_is_conditional_public_data(text: str) -> bool:
    """Keep `possible_outlook` conditional and limited to later data reads."""
    lowered = text.lower()
    has_public_data_scope = ("공개" in text and "데이터" in text) or (
        "public" in lowered and "data" in lowered
    )
    return has_public_data_scope and bool(_CONDITIONAL_OUTLOOK_PATTERN.search(text))


def run_semantic_checks(content: ReportContent, inputs: ReportPromptInputs) -> SafetyFilterResult:
    """Cross-field validation beyond phrase/pattern scanning: exact
    deterministic caution-literal match, metric consistency, exact
    possible_drivers literal match, and the external_context candidate-not-
    cause qualifier."""
    expected_caution = CAUTION_NOTE_BY_LEVEL.get(inputs.confidence_level)
    if expected_caution is None or content.caution_note != expected_caution:
        return SafetyFilterResult(
            passed=False, rule="caution_note_literal_mismatch", field="caution_note"
        )

    if not _current_data_reading_matches_inputs(content.current_data_reading, inputs):
        return SafetyFilterResult(
            passed=False,
            rule="current_data_reading_metric_mismatch",
            field="current_data_reading",
        )

    if not _has_public_participant_data_scope(content.current_data_reading):
        return SafetyFilterResult(
            passed=False,
            rule="current_data_reading_missing_public_participant_scope",
            field="current_data_reading",
        )

    if not _possible_outlook_is_conditional_public_data(content.possible_outlook):
        return SafetyFilterResult(
            passed=False,
            rule="possible_outlook_missing_conditional_public_data_scope",
            field="possible_outlook",
        )

    if content.possible_drivers != build_possible_drivers(inputs):
        return SafetyFilterResult(
            passed=False, rule="possible_drivers_literal_mismatch", field="possible_drivers"
        )

    if content.external_context is not None and not _external_context_has_required_qualifier(
        content.external_context
    ):
        return SafetyFilterResult(
            passed=False,
            rule="external_context_missing_candidate_not_cause_qualifier",
            field="external_context",
        )

    return SafetyFilterResult(passed=True)
