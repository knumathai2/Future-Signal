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
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

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
- In Korean, name that source only with the exact no-space compound
  "공개 예측시장 참여자 데이터". Never write "예측 시장" with a space and
  never use "예측" in any other phrase.
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

Before returning the JSON, verify these trimmed Unicode character counts:
- issue_overview: 30-600 characters
- current_data_reading: 50-700 characters and includes the exact Korean phrase
  "공개 예측시장 참여자 데이터"
- possible_outlook: 60-700 characters
Do not return a field below its minimum. Keep each field to 1-5 sentences.

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


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None


def _usage_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    data = getattr(value, "__dict__", None)
    return data if isinstance(data, Mapping) else {}


def _parse_llm_usage(value: object) -> LLMUsage:
    usage = _usage_mapping(value)
    cost = usage.get("cost")
    return LLMUsage(
        input_tokens=int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or usage.get("output_tokens") or 0),
        cost_usd=float(cost) if cost is not None else None,
    )


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
        self.usage_records: list[LLMUsage] = []

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
            raise LLMCallError(f"{self._provider_name} call failed: {type(exc).__name__}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMCallError(f"Empty response from {self._provider_name}.")
        self.usage_records.append(_parse_llm_usage(getattr(response, "usage", None)))
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
    "필요한 24시간 또는 7일 비교 지점 중 하나 이상이 없어 방향, 크기, 연속성을 판단할 수 없습니다."
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
        ", 수동 검토를 마친 맥락 후보의 기록 날짜" if _has_reviewed_candidate(inputs) else ""
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
        inputs.change_24h is not None and abs(inputs.change_24h) > CAUTION_HIGH_VOLATILITY_THRESHOLD
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
        for phrase, pattern in zip(KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(passed=False, rule=f"banned_phrase:{phrase}", field=field)
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


def _current_data_reading_matches_inputs(text: str, inputs: ReportPromptInputs) -> bool:
    """Reject metric-bearing model prose that contradicts structured inputs.

    The model may omit a metric when it uses a neutral non-numeric sentence,
    but every percentage or percentage-point value it does state must match a
    current value or available 24h/7d change. This prevents unsupported values
    from reaching storage without forcing one exact Korean sentence shape.
    """
    percent_values = _parse_numeric_tokens(_PERCENT_VALUE_PATTERN, text)
    if any(
        not _approximately_matches(value, inputs.current_value * 100) for value in percent_values
    ):
        return False

    available_changes = [
        change * 100 for change in (inputs.change_24h, inputs.change_7d) if change is not None
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
    korean_scope = "공개" in text and "데이터" in text and ("참여자" in text or "예측시장" in text)
    english_scope = (
        "public" in lowered
        and "data" in lowered
        and ("participant" in lowered or "prediction market" in lowered)
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


# --------------------------------------------------------------------------
# ADR-038 v4 evidence-grounded report contract.
# --------------------------------------------------------------------------

V4_PROMPT_VERSION = "v4"
V4_RELATIONSHIP_BOUNDARY = (
    "관찰된 움직임은 공개 데이터에 기록된 흐름이며, 현실의 결과 또는 함께 제시된 "
    "공개 정보와의 관계를 입증하지 않습니다."
)
V4_SYSTEM_PROMPT = """\
You write exactly two concise Korean fields for an evidence-grounded public
issue report: issue_overview and what_to_check. Use only the supplied structured
text. Do not add numbers, dates, URLs, source names, entities, outcomes, causes,
relationships, forecasts, or actions that are absent from the inputs. Never
state that public information explains a data movement. Return strict JSON and
no other text. Both values must be Korean prose strings between 30 and 600
characters; never return an array, object, or null for either field.

Korean safety rules:
- Describe the documented issue as a condition to check, never as a forecast.
- Never use "예측" except inside the exact no-space compound "예측시장".
- Never use 전망, 확정, 추천, 기회, 가능성이 높다, or 가능성이 낮다.
- Never suggest an action or imply that a real-world result will occur.
- Do not mention any data platform, market, participant dataset, probability,
  reflected value, or numeric movement; deterministic fields add those facts.
- Never write digits or numeric expressions in either field.
- Prefer the neutral shape "이 이슈는 ... 확인되는지를 살펴봅니다."."""


class V4ContextSource(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    citation_id: str
    title: str
    url: str
    canonical_url: str
    domain: str
    source_type: Literal["official", "independent_secondary"]
    content_hash: str


class V4VerifiedCandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: uuid.UUID
    title: str
    event_at: datetime
    neutral_summary: str
    sources: list[V4ContextSource] = Field(min_length=1)


class ResolutionRulesInput(BaseModel):
    """Provenance-preserving market definition supplied to grounded writers."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    condition_text: str | None
    deadline: datetime | None
    exclusions: list[str] = Field(default_factory=list)
    resolution_source: str | None
    source_description_hash: str | None
    rules_hash: str
    collected_at: datetime


class V4ReportInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    market_id: uuid.UUID
    metric_id: int
    episode_at: datetime
    data_as_of: datetime
    title: str
    description: str
    category: str
    outcome_label: str | None
    end_date: datetime | None
    current_value: float = Field(ge=0, le=1)
    change_24h: float | None
    change_7d: float | None
    confidence_level: str
    volume_24h: float | None
    liquidity: float | None
    context_candidates: list[V4VerifiedCandidateInput] = Field(max_length=3)
    resolution_rules: ResolutionRulesInput | None = None
    value_24h_ago: float | None = Field(default=None, ge=0, le=1)
    value_24h_ago_at: datetime | None = None
    value_7d_ago: float | None = Field(default=None, ge=0, le=1)
    value_7d_ago_at: datetime | None = None

    @model_validator(mode="after")
    def validate_reference_values(self) -> "V4ReportInputs":
        """Require paired reference values/times and metric consistency."""
        for label, value, captured_at, change in (
            ("24h", self.value_24h_ago, self.value_24h_ago_at, self.change_24h),
            ("7d", self.value_7d_ago, self.value_7d_ago_at, self.change_7d),
        ):
            if (value is None) != (captured_at is None):
                raise ValueError(f"{label} reference value and timestamp must be paired")
            if value is not None:
                expected = round(self.current_value - value, 4)
                if change is None or abs(expected - change) > 0.0001:
                    raise ValueError(f"{label} reference value does not match stored change")
        return self


class V4LLMFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_overview: str = Field(min_length=30, max_length=600)
    what_to_check: str = Field(min_length=30, max_length=600)

    @field_validator("*")
    @classmethod
    def limit_sentence_count(cls, value: str) -> str:
        if _sentence_count(value) > 5:
            raise ValueError("V4 LLM fields must contain at most five sentences.")
        return value


class V4ReportContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_overview: str = Field(min_length=30, max_length=600)
    observed_change: str = Field(min_length=50, max_length=900)
    context_summary: str | None = Field(default=..., min_length=40, max_length=1800)
    relationship_boundary: str = Field(min_length=50, max_length=500)
    what_to_check: str = Field(min_length=30, max_length=600)
    data_limitations: str = Field(min_length=50, max_length=900)
    caution_note: str = Field(min_length=120, max_length=700)

    @field_validator("*")
    @classmethod
    def limit_sentence_count(cls, value: str | None) -> str | None:
        if value is not None and _sentence_count(value) > 5:
            raise ValueError("V4 report fields must contain at most five sentences.")
        return value


class V4StoredReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_at: datetime
    content: V4ReportContent
    evidence_refs: list[str] = Field(min_length=1, max_length=4)
    context_candidate_ids: list[uuid.UUID] = Field(max_length=3)


def build_v4_prompt(inputs: V4ReportInputs) -> tuple[str, str]:
    candidates = [
        {
            "title": candidate.title,
            "event_at": candidate.event_at.isoformat(),
            "neutral_summary": candidate.neutral_summary,
        }
        for candidate in inputs.context_candidates
    ]
    payload = {
        "title": inputs.title,
        "category": inputs.category,
        "outcome_label": inputs.outcome_label,
        "end_date": inputs.end_date.isoformat() if inputs.end_date else None,
        "verified_context_candidates": candidates,
    }
    user_prompt = (
        "Return JSON with exactly issue_overview and what_to_check. "
        "Both values are Korean prose strings of 30-600 characters, never arrays. "
        "Do not write any digits or numeric expressions. "
        "The overview explains only the documented issue. The check field lists "
        "only later source/data items to verify and never suggests an action.\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    return V4_SYSTEM_PROMPT, user_prompt


def parse_v4_llm_fields(raw_text: str) -> V4LLMFields | None:
    try:
        return V4LLMFields.model_validate_json(raw_text)
    except ValidationError:
        return None


def build_v4_observed_change(inputs: V4ReportInputs) -> str:
    parts = [
        "데이터 기준 시각 "
        f"{inputs.data_as_of.isoformat()}에 공개 예측시장 참여자 데이터에 반영된 "
        f"기대값은 {inputs.current_value * 100:.1f}%입니다."
    ]
    comparisons: list[str] = []
    if inputs.change_24h is not None:
        comparisons.append(f"24시간 변화 {inputs.change_24h * 100:+.1f}퍼센트포인트")
    if inputs.change_7d is not None:
        comparisons.append(f"7일 변화 {inputs.change_7d * 100:+.1f}퍼센트포인트")
    if comparisons:
        parts.append("관찰된 비교값은 " + ", ".join(comparisons) + "입니다.")
    else:
        parts.append("고정 비교 구간의 값은 이력 부족으로 제시하지 않습니다.")
    return " ".join(parts)


def build_v4_context_summary(inputs: V4ReportInputs) -> str | None:
    if not inputs.context_candidates:
        return None
    summaries = " ".join(candidate.neutral_summary for candidate in inputs.context_candidates)
    return "같은 검토 구간에 기록된 공개 정보 후보를 근거 범위 안에서 정리했습니다. " + summaries


def build_v4_data_limitations(inputs: V4ReportInputs) -> str:
    limitations = [
        "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다.",
        "수치와 맥락은 해당 기준 시각에 저장된 근거 범위에서만 해석해야 합니다.",
    ]
    if inputs.change_24h is None or inputs.change_7d is None:
        limitations.append("고정 비교 구간 가운데 일부는 충분한 이력이 없습니다.")
    if (
        inputs.volume_24h is None
        or inputs.volume_24h < CAUTION_LOW_ACTIVITY_VOLUME_THRESHOLD
        or inputs.liquidity is None
        or inputs.liquidity < CAUTION_LOW_ACTIVITY_LIQUIDITY_THRESHOLD
    ):
        limitations.append("활동량 또는 유동성이 설정된 하한보다 낮거나 확인되지 않았습니다.")
    if inputs.change_24h is not None and abs(inputs.change_24h) > CAUTION_HIGH_VOLATILITY_THRESHOLD:
        limitations.append("24시간 변화 폭이 커서 단기 변동에 민감할 수 있습니다.")
    return " ".join(limitations)


def assemble_v4_report_content(
    inputs: V4ReportInputs, fields: V4LLMFields
) -> V4ReportContent | None:
    caution_note = build_caution_note(inputs.confidence_level)
    if caution_note is None:
        return None
    try:
        return V4ReportContent(
            issue_overview=fields.issue_overview,
            observed_change=build_v4_observed_change(inputs),
            context_summary=build_v4_context_summary(inputs),
            relationship_boundary=V4_RELATIONSHIP_BOUNDARY,
            what_to_check=fields.what_to_check,
            data_limitations=build_v4_data_limitations(inputs),
            caution_note=caution_note,
        )
    except ValidationError:
        return None


def build_v4_stored_payload(
    inputs: V4ReportInputs, content: V4ReportContent
) -> V4StoredReportPayload:
    candidate_ids = [candidate.id for candidate in inputs.context_candidates]
    return V4StoredReportPayload(
        episode_at=inputs.episode_at,
        content=content,
        evidence_refs=[f"metric:{inputs.metric_id}"]
        + [f"candidate:{candidate_id}" for candidate_id in candidate_ids],
        context_candidate_ids=candidate_ids,
    )


_URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)
_NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")


def _v4_llm_fields_use_only_input_numbers(fields: V4LLMFields, inputs: V4ReportInputs) -> bool:
    allowed_text = " ".join(
        value
        for value in (
            inputs.title,
            inputs.description,
            inputs.category,
            inputs.outcome_label,
            inputs.end_date.isoformat() if inputs.end_date else None,
            *(candidate.title for candidate in inputs.context_candidates),
            *(candidate.event_at.isoformat() for candidate in inputs.context_candidates),
        )
        if value
    )
    allowed_numbers = set(_NUMBER_PATTERN.findall(allowed_text))
    actual_numbers = set(_NUMBER_PATTERN.findall(f"{fields.issue_overview} {fields.what_to_check}"))
    return actual_numbers.issubset(allowed_numbers)


def run_v4_safety_and_semantic_checks(
    payload: V4StoredReportPayload,
    inputs: V4ReportInputs,
    llm_fields: V4LLMFields,
) -> SafetyFilterResult:
    for field_name, text in payload.content.model_dump().items():
        if text is None:
            continue
        lowered = text.lower()
        for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
            if pattern.search(lowered):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_phrase:{phrase}", field=field_name
                )
        for phrase, pattern in zip(KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_phrase:{phrase}", field=field_name
                )
        for pattern in (*BANNED_PATTERNS, *KOREAN_BANNED_PATTERNS):
            if pattern.search(text):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_pattern:{pattern.pattern}", field=field_name
                )

    if _URL_PATTERN.search(f"{llm_fields.issue_overview} {llm_fields.what_to_check}"):
        return SafetyFilterResult(passed=False, rule="llm_added_url", field="what_to_check")
    if not _v4_llm_fields_use_only_input_numbers(llm_fields, inputs):
        return SafetyFilterResult(passed=False, rule="llm_added_number", field="what_to_check")
    expected_refs = [f"metric:{inputs.metric_id}"] + [
        f"candidate:{candidate.id}" for candidate in inputs.context_candidates
    ]
    if payload.evidence_refs != expected_refs:
        return SafetyFilterResult(passed=False, rule="evidence_ref_mismatch")
    if payload.context_candidate_ids != [candidate.id for candidate in inputs.context_candidates]:
        return SafetyFilterResult(passed=False, rule="candidate_id_mismatch")
    if payload.content.observed_change != build_v4_observed_change(inputs):
        return SafetyFilterResult(passed=False, rule="metric_content_mismatch")
    if payload.content.context_summary != build_v4_context_summary(inputs):
        return SafetyFilterResult(passed=False, rule="context_content_mismatch")
    if payload.content.relationship_boundary != V4_RELATIONSHIP_BOUNDARY:
        return SafetyFilterResult(passed=False, rule="relationship_boundary_mismatch")
    if payload.content.caution_note != CAUTION_NOTE_BY_LEVEL.get(inputs.confidence_level):
        return SafetyFilterResult(passed=False, rule="caution_note_literal_mismatch")
    if inputs.context_candidates and payload.content.context_summary is None:
        return SafetyFilterResult(passed=False, rule="missing_context_summary")
    if not inputs.context_candidates and payload.content.context_summary is not None:
        return SafetyFilterResult(passed=False, rule="unexpected_context_summary")
    return SafetyFilterResult(passed=True)


# --------------------------------------------------------------------------
# ADR-048 v5 evidence-bounded structured narrative contract.
# --------------------------------------------------------------------------

V5_PROMPT_VERSION = "v5"
V5_SYSTEM_PROMPT = """\
Write a useful Korean issue summary from only the supplied structured evidence.
Return strict JSON with exactly six fields: executive_summary,
current_data_interpretation, conditional_scenarios, factors_to_check,
signals_to_watch, and evidence_synthesis.
Use natural, issue-specific prose. Do not write generic filler that could apply
to an unrelated issue. Do not add facts, names, dates, numbers, events, sources,
URLs, relationships, forecasts, or outcomes that are absent from the evidence.
Include the exact supplied market.title once in executive_summary so the lead
section remains auditable and issue-specific; explain it in natural Korean
around that unchanged title.
Never state or imply that a cited event explains an observed data movement.
Do not use the Korean words 원인, 전망, 확정, 추천, or 수익 anywhere, even in
negative or cautionary sentences. Use 배경은 확인되지 않았습니다, 조건부
시나리오, 현실 결과를 뜻하지 않습니다, or independently verified wording
instead. Do not number scenarios or checklist items in the JSON text. Use only
the exact numbers and dates supplied in market, observed_data, or verified
candidate evidence; do not calculate, round, or introduce counts.
Do not say 상승이 이어진다, 하락이 이어진다, 움직임이 계속된다, or any
equivalent future direction. Scenarios may describe only whether the documented
market condition is confirmed, partially documented, or not confirmed.
Prefer the supplied display_value_percent and display_change_*_percentage_points
when writing Korean prose. Do not expose the internal confidence_level enum or
raw 0-to-1 decimals when a display value is supplied. Factors and watch items
must stay tied to the named market condition, outcome label, end date, or
verified evidence; do not fill them with generic data-methodology reminders.
Treat market.resolution_rules as the only source for resolution conditions,
deadlines, exceptions, and recognized source criteria. market.description is
display copy and is not a resolution rule. When resolution_rules is null or its
condition_text is null, do not introduce a procedure, institution, schedule, or
condition from general knowledge.
Scenario limits are binding: definition_complete allows one to four,
definition_partial allows one to three, definition_missing_with_context allows
one or two, and definition_missing_no_context requires exactly one limitation
scenario. In the last case, state only that the detailed resolution definition
is unavailable and do not add a procedural path.
conditional_scenarios must contain the number of distinct items allowed by
input_completeness. Each item must
have a short title and a narrative beginning with a Korean conditional expression
such as "만약" and may describe only conditions present in the supplied market
definition or verified evidence. factors_to_check and signals_to_watch must be
concrete issue-specific arrays, each item pairing a title with an explanation.
evidence_synthesis must be null when verified_context_candidates is empty and
must be grounded only in those candidates when they exist. Return JSON only.
"""


class V5ConditionalScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=100)
    narrative: str = Field(min_length=30, max_length=900)

    @field_validator("narrative")
    @classmethod
    def require_conditional_language(cls, value: str) -> str:
        if not any(token in value for token in ("만약", "경우", "확인된다면", "확인되지 않는다면")):
            raise ValueError("V5 scenarios must use explicit conditional language.")
        if _sentence_count(value) > 5:
            raise ValueError("V5 scenario narratives must contain at most five sentences.")
        return value


class V5BriefingItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=120)
    explanation: str = Field(min_length=20, max_length=700)

    @field_validator("explanation")
    @classmethod
    def limit_sentence_count(cls, value: str) -> str:
        if _sentence_count(value) > 4:
            raise ValueError("V5 briefing items must contain at most four sentences.")
        return value


class V5LLMFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    executive_summary: str = Field(min_length=80, max_length=1200)
    current_data_interpretation: str = Field(min_length=50, max_length=1200)
    conditional_scenarios: list[V5ConditionalScenario] = Field(min_length=1, max_length=4)
    factors_to_check: list[V5BriefingItem] = Field(min_length=2, max_length=6)
    signals_to_watch: list[V5BriefingItem] = Field(min_length=2, max_length=6)
    evidence_synthesis: str | None = Field(default=..., min_length=50, max_length=1800)

    @field_validator("executive_summary", "current_data_interpretation", "evidence_synthesis")
    @classmethod
    def limit_sentence_count(cls, value: str | None) -> str | None:
        if value is not None and _sentence_count(value) > 5:
            raise ValueError("V5 narrative fields must contain at most five sentences.")
        return value


class V5ReportContent(V5LLMFields):
    relationship_boundary: str = Field(min_length=50, max_length=500)
    data_limitations: str = Field(min_length=50, max_length=900)
    caution_note: str = Field(min_length=120, max_length=700)


class V5StoredReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_at: datetime
    content: V5ReportContent
    evidence_refs: list[str] = Field(min_length=1, max_length=4)
    context_candidate_ids: list[uuid.UUID] = Field(max_length=3)
    resolution_rules: ResolutionRulesInput | None = None


def determine_input_completeness(
    inputs: V4ReportInputs,
) -> Literal[
    "definition_complete",
    "definition_partial",
    "definition_missing_with_context",
    "definition_missing_no_context",
]:
    """Classify evidence availability deterministically before generation."""
    rules = inputs.resolution_rules
    if rules is not None and rules.condition_text:
        return "definition_complete" if rules.deadline is not None else "definition_partial"
    if inputs.context_candidates:
        return "definition_missing_with_context"
    return "definition_missing_no_context"


def _scenario_count_matches_completeness(
    fields: V5LLMFields, inputs: V4ReportInputs
) -> bool:
    count = len(fields.conditional_scenarios)
    minimum, maximum = {
        "definition_complete": (1, 4),
        "definition_partial": (1, 3),
        "definition_missing_with_context": (1, 2),
        "definition_missing_no_context": (1, 1),
    }[determine_input_completeness(inputs)]
    return minimum <= count <= maximum


def build_v5_prompt(inputs: V4ReportInputs) -> tuple[str, str]:
    payload = {
        "input_completeness": determine_input_completeness(inputs),
        "market": {
            "title": inputs.title,
            "description": inputs.description,
            "category": inputs.category,
            "outcome_label": inputs.outcome_label,
            "end_date": inputs.end_date.isoformat() if inputs.end_date else None,
            "resolution_rules": (
                inputs.resolution_rules.model_dump(mode="json")
                if inputs.resolution_rules is not None
                else None
            ),
        },
        "observed_data": {
            "data_as_of": inputs.data_as_of.isoformat(),
            "current_value": inputs.current_value,
            "display_value_percent": round(inputs.current_value * 100, 4),
            "change_24h": inputs.change_24h,
            "change_7d": inputs.change_7d,
            "display_change_24h_percentage_points": (
                round(inputs.change_24h * 100, 4) if inputs.change_24h is not None else None
            ),
            "display_change_7d_percentage_points": (
                round(inputs.change_7d * 100, 4) if inputs.change_7d is not None else None
            ),
            "confidence_level": inputs.confidence_level,
            "value_24h_ago": inputs.value_24h_ago,
            "value_24h_ago_at": (
                inputs.value_24h_ago_at.isoformat() if inputs.value_24h_ago_at else None
            ),
            "value_7d_ago": inputs.value_7d_ago,
            "value_7d_ago_at": (
                inputs.value_7d_ago_at.isoformat() if inputs.value_7d_ago_at else None
            ),
        },
        "verified_context_candidates": [
            {
                "title": candidate.title,
                "event_at": candidate.event_at.isoformat(),
                "neutral_summary": candidate.neutral_summary,
                "sources": [
                    {
                        "title": source.title,
                        "domain": source.domain,
                        "source_type": source.source_type,
                    }
                    for source in candidate.sources
                ],
            }
            for candidate in inputs.context_candidates
        ],
    }
    return V5_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_v5_llm_fields(raw_text: str) -> V5LLMFields | None:
    try:
        return V5LLMFields.model_validate_json(raw_text)
    except ValidationError:
        return None


def assemble_v5_report_content(
    inputs: V4ReportInputs, fields: V5LLMFields
) -> V5ReportContent | None:
    caution_note = build_caution_note(inputs.confidence_level)
    if caution_note is None:
        return None
    try:
        return V5ReportContent(
            **fields.model_dump(),
            relationship_boundary=V4_RELATIONSHIP_BOUNDARY,
            data_limitations=build_v4_data_limitations(inputs),
            caution_note=caution_note,
        )
    except ValidationError:
        return None


def build_v5_stored_payload(
    inputs: V4ReportInputs, content: V5ReportContent
) -> V5StoredReportPayload:
    candidate_ids = [candidate.id for candidate in inputs.context_candidates]
    return V5StoredReportPayload(
        episode_at=inputs.episode_at,
        content=content,
        evidence_refs=[f"metric:{inputs.metric_id}"]
        + [f"candidate:{candidate_id}" for candidate_id in candidate_ids],
        context_candidate_ids=candidate_ids,
        resolution_rules=inputs.resolution_rules,
    )


def _normalized_specific_tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"[A-Za-z]{3,}|[가-힣]{2,}", text)
        if token.casefold()
        not in {"this", "will", "issue", "market", "whether", "대한", "관련", "이슈"}
    }


def _v5_is_issue_specific(fields: V5LLMFields, inputs: V4ReportInputs) -> bool:
    input_tokens = _normalized_specific_tokens(
        " ".join(
            filter(
                None,
                (
                    inputs.title,
                    inputs.description,
                    inputs.outcome_label,
                    inputs.resolution_rules.condition_text
                    if inputs.resolution_rules is not None
                    else None,
                ),
            )
        )
    )
    # The lead section must itself identify the issue. A specific name hidden in
    # a later checklist must not rescue a reusable, generic executive summary.
    authored_tokens = _normalized_specific_tokens(fields.executive_summary)
    return bool(input_tokens & authored_tokens)


def _v5_authored_text(fields: V5LLMFields) -> str:
    values = [fields.executive_summary, fields.current_data_interpretation]
    values.extend(f"{item.title} {item.narrative}" for item in fields.conditional_scenarios)
    values.extend(f"{item.title} {item.explanation}" for item in fields.factors_to_check)
    values.extend(f"{item.title} {item.explanation}" for item in fields.signals_to_watch)
    if fields.evidence_synthesis is not None:
        values.append(fields.evidence_synthesis)
    return " ".join(values)


def _v5_has_excessive_duplication(fields: V5LLMFields) -> bool:
    values = [
        fields.executive_summary,
        fields.current_data_interpretation,
    ]
    values.extend(item.narrative for item in fields.conditional_scenarios)
    values.extend(item.explanation for item in fields.factors_to_check)
    values.extend(item.explanation for item in fields.signals_to_watch)
    if fields.evidence_synthesis is not None:
        values.append(fields.evidence_synthesis)
    normalized = [re.sub(r"\s+", " ", value).strip().casefold() for value in values]
    return len(normalized) != len(set(normalized))


def _v5_uses_only_evidence_numbers(fields: V5LLMFields, inputs: V4ReportInputs) -> bool:
    allowed_parts = [
        inputs.title,
        inputs.description,
        inputs.outcome_label,
        inputs.end_date.isoformat() if inputs.end_date else None,
        inputs.data_as_of.isoformat(),
        str(inputs.current_value),
        str(inputs.current_value * 100),
        "24 7",
        str(inputs.value_24h_ago) if inputs.value_24h_ago is not None else None,
        inputs.value_24h_ago_at.isoformat() if inputs.value_24h_ago_at else None,
        str(inputs.value_7d_ago) if inputs.value_7d_ago is not None else None,
        inputs.value_7d_ago_at.isoformat() if inputs.value_7d_ago_at else None,
    ]
    if inputs.resolution_rules is not None:
        allowed_parts.extend(
            (
                inputs.resolution_rules.condition_text,
                inputs.resolution_rules.deadline.isoformat()
                if inputs.resolution_rules.deadline
                else None,
                *inputs.resolution_rules.exclusions,
            )
        )
    for change in (inputs.change_24h, inputs.change_7d):
        if change is not None:
            allowed_parts.extend((str(change), str(change * 100)))
    allowed_parts.extend(
        f"{candidate.title} {candidate.event_at.isoformat()} "
        f"{candidate.neutral_summary} " + " ".join(source.title for source in candidate.sources)
        for candidate in inputs.context_candidates
    )
    allowed_text = " ".join(part for part in allowed_parts if part)
    allowed = set(_NUMBER_PATTERN.findall(allowed_text))
    actual = set(_NUMBER_PATTERN.findall(_v5_authored_text(fields)))
    return actual.issubset(allowed)


def run_v5_safety_and_semantic_checks(
    payload: V5StoredReportPayload,
    inputs: V4ReportInputs,
    llm_fields: V5LLMFields,
) -> SafetyFilterResult:
    for field_name, value in payload.content.model_dump().items():
        texts = [value] if isinstance(value, str) else []
        if isinstance(value, list):
            texts = [str(part) for item in value for part in item.values()]
        for text in texts:
            if not text:
                continue
            lowered = text.lower()
            for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
                if pattern.search(lowered):
                    return SafetyFilterResult(False, f"banned_phrase:{phrase}", field_name)
            for phrase, pattern in zip(
                KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True
            ):
                if pattern.search(text):
                    return SafetyFilterResult(False, f"banned_phrase:{phrase}", field_name)
            for pattern in (*BANNED_PATTERNS, *KOREAN_BANNED_PATTERNS):
                if pattern.search(text):
                    return SafetyFilterResult(
                        False, f"banned_pattern:{pattern.pattern}", field_name
                    )

    authored_text = _v5_authored_text(llm_fields)
    if _URL_PATTERN.search(authored_text):
        return SafetyFilterResult(False, "llm_added_url")
    if not _v5_uses_only_evidence_numbers(llm_fields, inputs):
        return SafetyFilterResult(False, "unsupported_number")
    if not _v5_is_issue_specific(llm_fields, inputs):
        return SafetyFilterResult(False, "generic_summary", "executive_summary")
    if llm_fields.executive_summary.count(inputs.title) != 1:
        return SafetyFilterResult(
            False,
            "exact_title_occurrence_mismatch",
            "executive_summary",
        )
    if _v5_has_excessive_duplication(llm_fields):
        return SafetyFilterResult(False, "duplicate_narrative_fields")
    if not _scenario_count_matches_completeness(llm_fields, inputs):
        return SafetyFilterResult(False, "scenario_count_evidence_mismatch")
    if bool(inputs.context_candidates) != (llm_fields.evidence_synthesis is not None):
        return SafetyFilterResult(False, "evidence_synthesis_presence_mismatch")
    expected_refs = [f"metric:{inputs.metric_id}"] + [
        f"candidate:{candidate.id}" for candidate in inputs.context_candidates
    ]
    if payload.evidence_refs != expected_refs:
        return SafetyFilterResult(False, "evidence_ref_mismatch")
    if payload.context_candidate_ids != [candidate.id for candidate in inputs.context_candidates]:
        return SafetyFilterResult(False, "candidate_id_mismatch")
    if payload.content.relationship_boundary != V4_RELATIONSHIP_BOUNDARY:
        return SafetyFilterResult(False, "relationship_boundary_mismatch")
    if payload.content.data_limitations != build_v4_data_limitations(inputs):
        return SafetyFilterResult(False, "data_limitations_mismatch")
    if payload.content.caution_note != CAUTION_NOTE_BY_LEVEL.get(inputs.confidence_level):
        return SafetyFilterResult(False, "caution_note_literal_mismatch")
    return SafetyFilterResult(True)
