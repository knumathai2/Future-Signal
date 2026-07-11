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
import unicodedata
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal, Protocol

from openai import OpenAI, OpenAIError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

from app.core.signal_detection import EXPECTATION_SHIFT_THRESHOLD
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


class RecentHistorySummary(BaseModel):
    """Deterministic bounded summary of stored snapshots, never model-computed."""

    model_config = ConfigDict(extra="forbid")

    start_at: datetime
    start_value: float = Field(ge=0, le=1)
    end_at: datetime
    end_value: float = Field(ge=0, le=1)
    min_value: float = Field(ge=0, le=1)
    max_value: float = Field(ge=0, le=1)
    sample_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_summary(self) -> "RecentHistorySummary":
        if self.start_at > self.end_at:
            raise ValueError("history summary start must not follow end")
        if self.min_value > self.max_value:
            raise ValueError("history summary minimum must not exceed maximum")
        if not self.min_value <= self.start_value <= self.max_value:
            raise ValueError("history start value must be inside the range")
        if not self.min_value <= self.end_value <= self.max_value:
            raise ValueError("history end value must be inside the range")
        return self


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
    recent_history_summary: RecentHistorySummary | None = None

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
Every conditional scenario, factor, and watch item must include exactly one
basis value: market_definition, observed_data, verified_context, or
data_limitation. Use market_definition only when condition_text exists, use
verified_context only when verified candidates exist, and use data_limitation
only when observed_data.missing_fields is non-empty.
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
    basis: Literal["market_definition", "observed_data", "verified_context", "data_limitation"]

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
    basis: Literal["market_definition", "observed_data", "verified_context", "data_limitation"]

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


def build_recent_history_summary(
    points: list[tuple[datetime, float]],
) -> RecentHistorySummary | None:
    """Summarize ordered or unordered stored points with deterministic math."""
    if not points:
        return None
    ordered = sorted(points, key=lambda point: point[0])
    values = [float(value) for _, value in ordered]
    return RecentHistorySummary(
        start_at=ordered[0][0],
        start_value=values[0],
        end_at=ordered[-1][0],
        end_value=values[-1],
        min_value=min(values),
        max_value=max(values),
        sample_count=len(values),
    )


def build_v5_missing_fields(inputs: V4ReportInputs) -> list[str]:
    """List evidence gaps deterministically for the writer and audit tests."""
    missing: list[str] = []
    if inputs.resolution_rules is None or not inputs.resolution_rules.condition_text:
        missing.append("market.resolution_rules.condition_text")
    if inputs.end_date is None and (
        inputs.resolution_rules is None or inputs.resolution_rules.deadline is None
    ):
        missing.append("market.deadline")
    for label, change, value, captured_at in (
        ("24h", inputs.change_24h, inputs.value_24h_ago, inputs.value_24h_ago_at),
        ("7d", inputs.change_7d, inputs.value_7d_ago, inputs.value_7d_ago_at),
    ):
        if change is None or value is None or captured_at is None:
            missing.append(f"observed_data.{label}_reference")
    if inputs.volume_24h is None:
        missing.append("observed_data.volume_24h")
    if inputs.liquidity is None:
        missing.append("observed_data.liquidity")
    if inputs.recent_history_summary is None:
        missing.append("observed_data.recent_history_summary")
    return missing


def _scenario_count_matches_completeness(fields: V5LLMFields, inputs: V4ReportInputs) -> bool:
    count = len(fields.conditional_scenarios)
    minimum, maximum = {
        "definition_complete": (1, 4),
        "definition_partial": (1, 3),
        "definition_missing_with_context": (1, 2),
        "definition_missing_no_context": (1, 1),
    }[determine_input_completeness(inputs)]
    return minimum <= count <= maximum


def _basis_values_match_available_evidence(fields: V5LLMFields, inputs: V4ReportInputs) -> bool:
    basis_values = [item.basis for item in fields.conditional_scenarios]
    basis_values.extend(item.basis for item in fields.factors_to_check)
    basis_values.extend(item.basis for item in fields.signals_to_watch)
    if "market_definition" in basis_values and (
        inputs.resolution_rules is None or not inputs.resolution_rules.condition_text
    ):
        return False
    if "verified_context" in basis_values and not inputs.context_candidates:
        return False
    if "data_limitation" in basis_values and not build_v5_missing_fields(inputs):
        return False
    return True


_GROUNDED_DETAIL_TERMS: tuple[str, ...] = (
    "위원회",
    "본회의",
    "표결",
    "수정안",
    "연방준비제도",
    "한국은행",
    "유럽중앙은행",
    "fomc",
    "금통위",
    "기준금리",
    "물가",
    "고용",
    "중재자",
    "중재",
    "합의문",
    "당사국",
    "committee",
    "plenary",
    "amendment",
    "federal reserve",
    "central bank meeting",
    "mediator",
    "agreement document",
)


def _v5_uses_only_supported_detail_terms(fields: V5LLMFields, inputs: V4ReportInputs) -> bool:
    """Reject high-risk procedural detail absent from structured evidence.

    This bounded MVP gate complements numeric/date/URL validation. A term may
    appear when it is present in the source title, resolution definition, or
    verified candidate evidence, but not merely from model background knowledge.
    """
    evidence_parts = [inputs.title, inputs.outcome_label or ""]
    if inputs.resolution_rules is not None:
        evidence_parts.extend(
            [
                inputs.resolution_rules.condition_text or "",
                *inputs.resolution_rules.exclusions,
            ]
        )
    for candidate in inputs.context_candidates:
        evidence_parts.extend((candidate.title, candidate.neutral_summary))
    evidence = " ".join(evidence_parts).casefold()
    authored = _v5_authored_text(fields).casefold()
    return all(term not in authored or term in evidence for term in _GROUNDED_DETAIL_TERMS)


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
            "volume_24h": inputs.volume_24h,
            "liquidity": inputs.liquidity,
            "recent_history_summary": (
                inputs.recent_history_summary.model_dump(mode="json")
                if inputs.recent_history_summary is not None
                else None
            ),
            "missing_fields": build_v5_missing_fields(inputs),
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
        str(inputs.volume_24h) if inputs.volume_24h is not None else None,
        str(inputs.liquidity) if inputs.liquidity is not None else None,
    ]
    if inputs.recent_history_summary is not None:
        allowed_parts.extend(
            str(value) for value in inputs.recent_history_summary.model_dump(mode="json").values()
        )
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
    if not _basis_values_match_available_evidence(llm_fields, inputs):
        return SafetyFilterResult(False, "basis_evidence_mismatch")
    if not _v5_uses_only_supported_detail_terms(llm_fields, inputs):
        return SafetyFilterResult(False, "unsupported_procedural_detail")
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


# --------------------------------------------------------------------------
# ADR-050 v6 deterministic evidence-aware briefing contract.
# --------------------------------------------------------------------------

V6_PROMPT_VERSION = "v6"
V6ReportMode = Literal[
    "change_with_evidence",
    "change_without_evidence",
    "stable_with_evidence",
    "stable_without_evidence",
]
V6EvidenceBasis = Literal[
    "observed_data",
    "market_definition",
    "verified_context",
    "general_scenario",
    "data_limitation",
]

V6_SYSTEM_PROMPT = """\
Write concise Korean briefing blocks using only the supplied structured input.
Return exactly the JSON shape requested for selected_report_mode. Do not add
extra fields. The mode was selected by deterministic code and must be copied
exactly; never choose or change it.

Do not write any digits, dates, current values, change amounts, thresholds, or
resolution-rule wording in authored prose. Those appear once in deterministic
UI regions. Do not add current events, named-person status, concrete procedures,
relationships, forecasts, likelihood rankings, outcomes, or reader actions that
are absent from verified_context_candidates. General scenario blocks describe
only generic conditional possibilities and must use basis general_scenario;
they are not evidence of the current situation. Verified background may use
only verified_context_candidates and must copy their candidate_ids exactly.

Copy at least one value from required_issue_anchors exactly, preserving its
spelling, in the issue explanation or first scenario text. Translate the
surrounding prose and every other English term, not that anchor. Every
conditional scenario text must contain
one of 만약, 경우, 된다면, or 않는다면. In modes with materials_to_check, if
there are N conditional_scenarios, return exactly N materials, using each
scenario_index from 1 through N exactly once.

Never assert that verified material explains an observed movement. Never use
the Korean words 원인, 전망, 확정, 추천, 수익, 가능성 순위, or 행동 anywhere.
Do not reproduce the market resolution condition, deadline, exclusions, source
criteria, current value, metric date, or change amount. Keep every text field
issue-specific, non-causal, conditional where applicable, and complete Korean.
Return JSON only.
"""


class V6MarketDefinitionBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=30, max_length=900)
    basis: Literal["market_definition"]


class V6GeneralBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=30, max_length=900)
    basis: Literal["general_scenario"]


class V6VerifiedBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=30, max_length=1200)
    basis: Literal["verified_context"]
    candidate_ids: list[uuid.UUID] = Field(min_length=1, max_length=3)


class V6GeneralScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=100)
    text: str = Field(min_length=30, max_length=900)
    basis: Literal["general_scenario"]

    @field_validator("text")
    @classmethod
    def require_conditional_language(cls, value: str) -> str:
        if not any(token in value for token in ("만약", "경우", "된다면", "않는다면")):
            raise ValueError("V6 scenarios require explicit conditional language")
        return value


class V6VerifiedInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=100)
    text: str = Field(min_length=30, max_length=900)
    basis: Literal["verified_context"]
    candidate_ids: list[uuid.UUID] = Field(min_length=1, max_length=3)

    @field_validator("text")
    @classmethod
    def require_conditional_language(cls, value: str) -> str:
        if not any(token in value for token in ("만약", "경우", "된다면", "않는다면")):
            raise ValueError("V6 interpretations require explicit conditional language")
        return value


class V6MaterialToCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scenario_index: int = Field(ge=1, le=4)
    title: str = Field(min_length=2, max_length=120)
    text: str = Field(min_length=20, max_length=700)
    basis: Literal["general_scenario"]


class V6ChangeWithEvidenceBriefing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["change_with_evidence"]
    verified_background: V6VerifiedBlock
    conditional_interpretations: list[V6VerifiedInterpretation] = Field(min_length=1, max_length=4)


class V6ChangeWithoutEvidenceBriefing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["change_without_evidence"]
    conditional_scenarios: list[V6GeneralScenario] = Field(min_length=1, max_length=4)
    materials_to_check: list[V6MaterialToCheck] = Field(min_length=1, max_length=8)


class V6StableWithEvidenceBriefing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["stable_with_evidence"]
    issue_explanation: V6MarketDefinitionBlock
    verified_background: V6VerifiedBlock
    conditional_scenarios: list[V6GeneralScenario] = Field(min_length=1, max_length=4)


class V6StableWithoutEvidenceBriefing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["stable_without_evidence"]
    issue_explanation: V6GeneralBlock
    conditional_scenarios: list[V6GeneralScenario] = Field(min_length=1, max_length=4)
    materials_to_check: list[V6MaterialToCheck] = Field(min_length=1, max_length=8)


V6Briefing = Annotated[
    V6ChangeWithEvidenceBriefing
    | V6ChangeWithoutEvidenceBriefing
    | V6StableWithEvidenceBriefing
    | V6StableWithoutEvidenceBriefing,
    Field(discriminator="mode"),
]
_V6_BRIEFING_ADAPTER = TypeAdapter(V6Briefing)


class V6ObservedChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: int
    window: Literal["24h"]
    current_value: float = Field(ge=0, le=1)
    change_value: float | None
    significant: bool
    threshold: float = Field(ge=0, le=1)


class V6ResolutionReference(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["available", "unavailable"]
    condition_text: str | None
    deadline: datetime | None
    exclusions: list[str]
    source_url: str | None


class V6StoredReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_at: datetime
    report_mode: V6ReportMode
    observed_change: V6ObservedChange
    briefing: V6Briefing
    resolution_reference: V6ResolutionReference
    evidence_refs: list[str] = Field(min_length=1, max_length=4)
    context_candidate_ids: list[uuid.UUID] = Field(max_length=3)
    resolution_rules: ResolutionRulesInput | None = None
    relationship_boundary: str = Field(min_length=50, max_length=500)
    data_limitations: str = Field(min_length=50, max_length=900)
    caution_note: str = Field(min_length=120, max_length=700)


def has_v6_significant_change(inputs: V4ReportInputs) -> bool:
    """Reuse the existing signal rule without depending on cooldown rows."""
    return (
        inputs.confidence_level != "insufficient_data"
        and inputs.change_24h is not None
        and abs(inputs.change_24h) >= EXPECTATION_SHIFT_THRESHOLD
    )


def determine_v6_report_mode(inputs: V4ReportInputs) -> V6ReportMode:
    """Select the four-way report mode from independent deterministic facts."""
    changed = has_v6_significant_change(inputs)
    verified = bool(inputs.context_candidates)
    if changed and verified:
        return "change_with_evidence"
    if changed:
        return "change_without_evidence"
    if verified:
        return "stable_with_evidence"
    return "stable_without_evidence"


def build_v6_observed_change(inputs: V4ReportInputs) -> V6ObservedChange:
    return V6ObservedChange(
        metric_id=inputs.metric_id,
        window="24h",
        current_value=inputs.current_value,
        change_value=inputs.change_24h,
        significant=has_v6_significant_change(inputs),
        threshold=EXPECTATION_SHIFT_THRESHOLD,
    )


def build_v6_resolution_reference(inputs: V4ReportInputs) -> V6ResolutionReference:
    rules = inputs.resolution_rules
    if rules is None or not rules.condition_text:
        return V6ResolutionReference(
            status="unavailable",
            condition_text=None,
            deadline=None,
            exclusions=[],
            source_url=None,
        )
    return V6ResolutionReference(
        status="available",
        condition_text=rules.condition_text,
        deadline=rules.deadline,
        exclusions=rules.exclusions,
        source_url=rules.resolution_source,
    )


def _v6_output_shape(mode: V6ReportMode) -> dict:
    verified_block = {
        "text": "string",
        "basis": "verified_context",
        "candidate_ids": ["exact supplied candidate UUID"],
    }
    general_scenario = {
        "title": "string",
        "text": "conditional string",
        "basis": "general_scenario",
    }
    material = {
        "scenario_index": 1,
        "title": "string",
        "text": "string",
        "basis": "general_scenario",
    }
    if mode == "change_with_evidence":
        return {
            "mode": mode,
            "verified_background": verified_block,
            "conditional_interpretations": [
                {**general_scenario, "basis": "verified_context", "candidate_ids": []}
            ],
        }
    if mode == "change_without_evidence":
        return {
            "mode": mode,
            "conditional_scenarios": [general_scenario],
            "materials_to_check": [material],
        }
    if mode == "stable_with_evidence":
        return {
            "mode": mode,
            "issue_explanation": {"text": "string", "basis": "market_definition"},
            "verified_background": verified_block,
            "conditional_scenarios": [general_scenario],
        }
    return {
        "mode": mode,
        "issue_explanation": {"text": "string", "basis": "general_scenario"},
        "conditional_scenarios": [general_scenario],
        "materials_to_check": [material],
    }


_V6_ANCHOR_STOPWORDS = {
    "will",
    "is",
    "are",
    "the",
    "before",
    "after",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "politics",
}


def _v6_required_issue_anchors(inputs: V4ReportInputs) -> list[str]:
    """Prefer proper names so Korean prose need not preserve generic English."""
    anchors: list[str] = []
    seen: set[str] = set()
    anchor_sources = [inputs.title] + [
        candidate.title for candidate in inputs.context_candidates
    ]
    for source in anchor_sources:
        for token in re.findall(r"[A-Za-z]{3,}", source):
            normalized = token.casefold()
            if (
                normalized in _V6_ANCHOR_STOPWORDS
                or not token[0].isupper()
                or normalized in seen
            ):
                continue
            anchors.append(token)
            seen.add(normalized)
    if anchors:
        return anchors[:6]

    fallback = _normalized_specific_tokens(
        " ".join(
            [inputs.title, inputs.category]
            + [candidate.title for candidate in inputs.context_candidates]
        )
    )
    return sorted(fallback)[:12]


def build_v6_prompt(inputs: V4ReportInputs) -> tuple[str, str]:
    """Expose no metric values or exact resolution-rule prose to the writer."""
    mode = determine_v6_report_mode(inputs)
    payload = {
        "selected_report_mode": mode,
        "required_output_shape": _v6_output_shape(mode),
        "issue": {
            "title": inputs.title,
            "category": inputs.category,
            "outcome_label": inputs.outcome_label,
            "has_stored_definition": bool(
                inputs.resolution_rules and inputs.resolution_rules.condition_text
            ),
        },
        "required_issue_anchors": _v6_required_issue_anchors(inputs),
        "generation_constraints": {
            "conditional_tokens": ["만약", "경우", "된다면", "않는다면"],
            "scenario_count_range": [1, 4],
            "material_mapping": (
                "Return exactly one materials_to_check item for every "
                "conditional_scenarios item and use each one-based "
                "scenario_index exactly once."
            ),
        },
        "verified_context_candidates": [
            {
                "id": str(candidate.id),
                "title": candidate.title,
                "neutral_summary": candidate.neutral_summary,
                "source_titles": [source.title for source in candidate.sources],
            }
            for candidate in inputs.context_candidates
        ],
    }
    return V6_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_v6_briefing(raw_text: str, expected_mode: V6ReportMode) -> V6Briefing | None:
    try:
        briefing = _V6_BRIEFING_ADAPTER.validate_json(raw_text)
    except ValidationError:
        return None
    return briefing if briefing.mode == expected_mode else None


def build_v6_stored_payload(
    inputs: V4ReportInputs, briefing: V6Briefing
) -> V6StoredReportPayload | None:
    caution = build_caution_note(inputs.confidence_level)
    if caution is None:
        return None
    candidate_ids = [candidate.id for candidate in inputs.context_candidates]
    try:
        return V6StoredReportPayload(
            episode_at=inputs.episode_at,
            report_mode=determine_v6_report_mode(inputs),
            observed_change=build_v6_observed_change(inputs),
            briefing=briefing,
            resolution_reference=build_v6_resolution_reference(inputs),
            evidence_refs=[f"metric:{inputs.metric_id}"]
            + [f"candidate:{candidate_id}" for candidate_id in candidate_ids],
            context_candidate_ids=candidate_ids,
            resolution_rules=inputs.resolution_rules,
            relationship_boundary=V4_RELATIONSHIP_BOUNDARY,
            data_limitations=build_v4_data_limitations(inputs),
            caution_note=caution,
        )
    except ValidationError:
        return None


def _v6_body_texts(briefing: V6Briefing) -> list[str]:
    if isinstance(briefing, V6ChangeWithEvidenceBriefing):
        return [briefing.verified_background.text] + [
            item.text for item in briefing.conditional_interpretations
        ]
    if isinstance(briefing, V6ChangeWithoutEvidenceBriefing):
        return [item.text for item in briefing.conditional_scenarios] + [
            item.text for item in briefing.materials_to_check
        ]
    if isinstance(briefing, V6StableWithEvidenceBriefing):
        return [
            briefing.issue_explanation.text,
            briefing.verified_background.text,
            *(item.text for item in briefing.conditional_scenarios),
        ]
    return [
        briefing.issue_explanation.text,
        *(item.text for item in briefing.conditional_scenarios),
        *(item.text for item in briefing.materials_to_check),
    ]


def _canonical_v6_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"\d+(?:[.,:/-]\d+)*", "#", normalized)
    normalized = re.sub(r"[^a-z가-힣#]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _v6_content_tokens(text: str) -> set[str]:
    return {
        token
        for token in _canonical_v6_text(text).split()
        if len(token) >= 2 and token not in {"만약", "경우", "대한", "관련", "자료"}
    }


def _v6_has_duplicate_bodies(briefing: V6Briefing) -> bool:
    bodies = _v6_body_texts(briefing)
    canonical = [_canonical_v6_text(body) for body in bodies]
    if len(canonical) != len(set(canonical)):
        return True
    for index, left in enumerate(bodies):
        left_tokens = _v6_content_tokens(left)
        for right in bodies[index + 1 :]:
            right_tokens = _v6_content_tokens(right)
            union = left_tokens | right_tokens
            if (
                min(len(left_tokens), len(right_tokens)) >= 4
                and union
                and len(left_tokens & right_tokens) / len(union) >= 0.82
            ):
                return True
    return False


def _v6_repeats_resolution_rule(briefing: V6Briefing, inputs: V4ReportInputs) -> bool:
    rules = inputs.resolution_rules
    if rules is None or not rules.condition_text:
        return False
    rule = _canonical_v6_text(rules.condition_text)
    rule_tokens = _v6_content_tokens(rules.condition_text)
    for body in _v6_body_texts(briefing):
        canonical = _canonical_v6_text(body)
        body_tokens = _v6_content_tokens(body)
        overlap = rule_tokens & body_tokens
        if rule and rule in canonical:
            return True
        if len(overlap) >= 4 and len(overlap) / max(1, len(rule_tokens)) >= 0.7:
            return True
    return False


def _v6_candidate_ids_match(briefing: V6Briefing, inputs: V4ReportInputs) -> bool:
    expected = [candidate.id for candidate in inputs.context_candidates]
    if isinstance(briefing, V6ChangeWithEvidenceBriefing | V6StableWithEvidenceBriefing):
        if briefing.verified_background.candidate_ids != expected:
            return False
    if isinstance(briefing, V6ChangeWithEvidenceBriefing):
        allowed = set(expected)
        return all(
            item.candidate_ids and set(item.candidate_ids).issubset(allowed)
            for item in briefing.conditional_interpretations
        )
    return True


def _v6_materials_cover_scenarios(briefing: V6Briefing) -> bool:
    if not isinstance(briefing, V6ChangeWithoutEvidenceBriefing | V6StableWithoutEvidenceBriefing):
        return True
    scenario_count = len(briefing.conditional_scenarios)
    indices = {item.scenario_index for item in briefing.materials_to_check}
    return indices == set(range(1, scenario_count + 1))


_UNSUPPORTED_CURRENT_FACT_PATTERN = re.compile(
    r"(?:현재|오늘|최근|지금|이번)\s*[^.!?]{0,40}"
    r"(?:발표|사임|취임|진행|발생|합의|승인|통과|결정|확인됐)"
)


def _v6_adds_unsupported_current_fact(briefing: V6Briefing) -> bool:
    """Block source-free prose that presents a recent state as current fact."""
    if isinstance(briefing, V6ChangeWithEvidenceBriefing | V6StableWithEvidenceBriefing):
        general_texts = [item.text for item in getattr(briefing, "conditional_scenarios", [])]
    else:
        general_texts = _v6_body_texts(briefing)
    return any(_UNSUPPORTED_CURRENT_FACT_PATTERN.search(text) for text in general_texts)


_V6_AUTHORED_DATE_PATTERN = re.compile(
    r"(?<![A-Za-z])(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)(?![A-Za-z])|"
    r"(?:기준일|마감일|시한|연말|연초|월말|월초)",
    re.IGNORECASE,
)


def _v6_repeats_authored_date(briefing: V6Briefing) -> bool:
    """Dates and deadlines belong to deterministic/reference UI regions only."""
    return any(_V6_AUTHORED_DATE_PATTERN.search(text) for text in _v6_body_texts(briefing))


def _v6_uses_unapproved_english(briefing: V6Briefing, inputs: V4ReportInputs) -> bool:
    """Allow supplied proper-name anchors, not generic English prose."""
    allowed = {anchor.casefold() for anchor in _v6_required_issue_anchors(inputs)}
    return any(
        token.casefold() not in allowed
        for text in _v6_body_texts(briefing)
        for token in re.findall(r"[A-Za-z]{3,}", text)
    )


def run_v6_safety_and_semantic_checks(
    payload: V6StoredReportPayload,
    inputs: V4ReportInputs,
    briefing: V6Briefing,
) -> SafetyFilterResult:
    """Validate mode, evidence, safety, duplication, and single-owner rules."""
    if payload.report_mode != determine_v6_report_mode(inputs):
        return SafetyFilterResult(False, "report_mode_mismatch")
    if briefing.mode != payload.report_mode:
        return SafetyFilterResult(False, "briefing_mode_mismatch")

    for text in _v6_body_texts(briefing):
        lowered = text.lower()
        for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
            if pattern.search(lowered):
                return SafetyFilterResult(False, f"banned_phrase:{phrase}")
        for phrase, pattern in zip(KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(False, f"banned_phrase:{phrase}")
        for pattern in (*BANNED_PATTERNS, *KOREAN_BANNED_PATTERNS):
            if pattern.search(text):
                return SafetyFilterResult(False, f"banned_pattern:{pattern.pattern}")
        if _URL_PATTERN.search(text):
            return SafetyFilterResult(False, "llm_added_url")
        if _NUMBER_PATTERN.search(text):
            return SafetyFilterResult(False, "deterministic_value_repeated")

    if _v6_has_duplicate_bodies(briefing):
        return SafetyFilterResult(False, "duplicate_narrative_fields")
    if _v6_repeats_resolution_rule(briefing, inputs):
        return SafetyFilterResult(False, "resolution_rule_repeated")
    if _v6_repeats_authored_date(briefing):
        return SafetyFilterResult(False, "authored_date_repeated")
    if _v6_uses_unapproved_english(briefing, inputs):
        return SafetyFilterResult(False, "non_korean_generic_term")
    if _v6_adds_unsupported_current_fact(briefing):
        return SafetyFilterResult(False, "unsupported_current_fact")
    if not _v6_candidate_ids_match(briefing, inputs):
        return SafetyFilterResult(False, "candidate_id_mismatch")
    if not _v6_materials_cover_scenarios(briefing):
        return SafetyFilterResult(False, "scenario_material_mismatch")

    authored = " ".join(_v6_body_texts(briefing))
    evidence_tokens = _normalized_specific_tokens(
        " ".join(
            [inputs.title, inputs.category]
            + [
                f"{candidate.title} {candidate.neutral_summary}"
                for candidate in inputs.context_candidates
            ]
        )
    )
    if not evidence_tokens & _normalized_specific_tokens(authored):
        return SafetyFilterResult(False, "generic_summary")

    expected_refs = [f"metric:{inputs.metric_id}"] + [
        f"candidate:{candidate.id}" for candidate in inputs.context_candidates
    ]
    if payload.evidence_refs != expected_refs:
        return SafetyFilterResult(False, "evidence_ref_mismatch")
    if payload.context_candidate_ids != [candidate.id for candidate in inputs.context_candidates]:
        return SafetyFilterResult(False, "candidate_id_mismatch")
    if payload.observed_change != build_v6_observed_change(inputs):
        return SafetyFilterResult(False, "observed_change_mismatch")
    if payload.resolution_reference != build_v6_resolution_reference(inputs):
        return SafetyFilterResult(False, "resolution_reference_mismatch")
    if payload.relationship_boundary != V4_RELATIONSHIP_BOUNDARY:
        return SafetyFilterResult(False, "relationship_boundary_mismatch")
    if payload.data_limitations != build_v4_data_limitations(inputs):
        return SafetyFilterResult(False, "data_limitations_mismatch")
    if payload.caution_note != CAUTION_NOTE_BY_LEVEL.get(inputs.confidence_level):
        return SafetyFilterResult(False, "caution_note_literal_mismatch")
    return SafetyFilterResult(True)


# --------------------------------------------------------------------------
# ADR-051 v7 positive-first, flexible evidence-linked writer contract.
# Public request/cache assembly is owned by TASK-102~105; this section is the
# provider-independent writer boundary only.
# --------------------------------------------------------------------------

V7_PROMPT_VERSION = "v7"
V7_POLICY_VERSION = "v7-positive-evidence-2"
V7_INPUT_SCHEMA_VERSION = "v7-writer-input-1"
V7SectionType = Literal[
    "issue_overview",
    "current_context",
    "market_data",
    "external_context",
    "uncertainties",
    "what_to_watch",
]
V7EvidenceKind = Literal[
    "market_definition",
    "metric",
    "observed_history",
    "context",
    "source",
    "data_limitation",
]
V7SourceLevel = Literal["A", "B", "C"]

V7_SYSTEM_PROMPT = """\
You are an issue briefing writer helping a general reader understand the
current issue quickly and accurately.

Begin by explaining what the issue is and why its stated condition matters.
Summarize the current situation using the supplied source material. Explain
the observed market-data movement in clear language while keeping market
observations and external-source information visibly distinct. Connect every
factual statement to the supplied evidence reference that supports it.

When the material supports more than one interpretation, present the
alternatives and explain what remains uncertain. Attribute statements to their
source when the source level or evidence requires attribution. Tell the reader
which announcements, documents, dates, or data updates would help clarify the
issue next.

Use natural, concrete Korean. Choose the number, order, titles, and paragraph
or bullet presentation of sections according to the available evidence. Omit
a category when no supplied evidence supports it. Return only the requested
JSON object.

Follow the requested JSON structure exactly with no extra fields. Return two
to eight sections. Every section must use one allowed section type, a 2-100
character title, either a 30-1800 character paragraph or one to eight bullet
items of 15-500 characters each, and one to twelve unique evidence references.

Use only exact evidence references supplied in the input. When a section uses
a `source:*` reference, include that source's `context:*` parent reference in
the same section. Do not write a URL in the headline, summary, section title,
paragraph, or bullet text; source links are attached separately by the
application.

Do not use any of these expressions in authored text: bet, buy, sell, trade,
position, long, short, profit, win rate, odds, copy trader, follow this user,
expert trader, best pick, recommended outcome, high-return opportunity,
guaranteed, guaranteed prediction, signal to act, recommend, recommendation,
베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 추천, 보장, 확정,
따라하기, 고수, 전문 트레이더, 고수익, 기회.

Express status and evidence sentences with 판정, 조건 충족 여부, 공식 결정,
and 관찰 범위 as the status nouns. Prefer describing metric direction. When a
numeric value helps, copy the supplied comparison window,
`current_value_percent`, or `change_*_pp` display value exactly and cite the
metric reference instead of calculating a new value. When a cited definition
includes an English month name, its ordinary Korean numeric-month rendering is
supported by that same reference.

Do not invent facts, sources, references, relationships, or future results.
Do not encourage the reader to take a financial or market action. Treat an
observed timing overlap as timing unless a supplied source explicitly supports
a stronger attributed statement.
"""


class V7EvidenceItem(BaseModel):
    """One exact evidence record exposed to the writer under an opaque ref."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ref: str = Field(min_length=3, max_length=200)
    kind: V7EvidenceKind
    text: str = Field(min_length=1, max_length=6000)
    parent_ref: str | None = Field(default=None, max_length=200)
    source_level: V7SourceLevel | None = None

    @model_validator(mode="after")
    def validate_ref_shape(self) -> "V7EvidenceItem":
        prefix = self.ref.partition(":")[0]
        if prefix != self.kind or not self.ref.partition(":")[2]:
            raise ValueError("V7 evidence ref prefix must match evidence kind")
        if self.kind == "source":
            if self.parent_ref is None or not self.parent_ref.startswith("context:"):
                raise ValueError("V7 source evidence requires a context parent ref")
            if self.source_level is None:
                raise ValueError("V7 source evidence requires an accepted source level")
        elif self.parent_ref is not None or self.source_level is not None:
            raise ValueError("Only V7 source evidence may carry parent ref or source level")
        return self


class V7WriterInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    category: str = Field(min_length=1, max_length=120)
    evidence: list[V7EvidenceItem] = Field(min_length=2, max_length=60)

    @model_validator(mode="after")
    def validate_evidence_bundle(self) -> "V7WriterInputs":
        refs = [item.ref for item in self.evidence]
        if len(refs) != len(set(refs)):
            raise ValueError("V7 writer evidence refs must be unique")
        ref_set = set(refs)
        if not any(item.kind == "market_definition" for item in self.evidence):
            raise ValueError("V7 writer inputs require market definition evidence")
        if not any(item.kind == "metric" for item in self.evidence):
            raise ValueError("V7 writer inputs require metric evidence")
        if any(item.parent_ref not in ref_set for item in self.evidence if item.parent_ref):
            raise ValueError("V7 source parent ref must exist in the same input bundle")
        return self


class V7WriterSection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: V7SectionType
    title: str = Field(min_length=2, max_length=100)
    format: Literal["paragraph", "bullets"]
    content: str | None = Field(default=None, min_length=30, max_length=1800)
    items: list[str] = Field(default_factory=list, max_length=8)
    evidence_refs: list[str] = Field(min_length=1, max_length=12)

    @field_validator("items")
    @classmethod
    def validate_item_bounds(cls, values: list[str]) -> list[str]:
        if any(not 15 <= len(value.strip()) <= 500 for value in values):
            raise ValueError("V7 bullet items must be 15-500 characters")
        return values

    @model_validator(mode="after")
    def validate_format_shape(self) -> "V7WriterSection":
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("V7 section evidence refs must be unique")
        if self.format == "paragraph" and (self.content is None or self.items):
            raise ValueError("V7 paragraph section requires content and no items")
        if self.format == "bullets" and (self.content is not None or not self.items):
            raise ValueError("V7 bullet section requires items and null content")
        return self


class V7WriterOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str = Field(min_length=10, max_length=120)
    summary: str = Field(min_length=40, max_length=900)
    sections: list[V7WriterSection] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def validate_section_mix(self) -> "V7WriterOutput":
        types = [section.type for section in self.sections]
        if not {"issue_overview", "current_context"} & set(types):
            raise ValueError("V7 output requires issue overview or current context")
        if types.count("market_data") > 1:
            raise ValueError("V7 output permits at most one market data section")
        return self


_V7_WRITER_ADAPTER = TypeAdapter(V7WriterOutput)


def build_v7_prompt(inputs: V7WriterInputs) -> tuple[str, str]:
    """Build a positive-first prompt with exact, opaque evidence refs."""
    output_shape = {
        "headline": "10-120 character string",
        "summary": "40-900 character string",
        "sections": [
            {
                "type": "one allowed broad section type",
                "title": "2-100 character string",
                "format": "paragraph or bullets",
                "content": "paragraph text or null",
                "items": ["bullet text; empty for paragraph"],
                "evidence_refs": ["exact supplied ref"],
            }
        ],
    }
    payload = {
        "policy_version": V7_POLICY_VERSION,
        "input_schema_version": V7_INPUT_SCHEMA_VERSION,
        "issue": {
            "id": str(inputs.issue_id),
            "title": inputs.title,
            "category": inputs.category,
        },
        "allowed_section_types": list(V7SectionType.__args__),
        "required_output_shape": output_shape,
        "evidence": [item.model_dump(mode="json") for item in inputs.evidence],
    }
    return V7_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_v7_writer_output(raw_text: str) -> V7WriterOutput | None:
    try:
        return _V7_WRITER_ADAPTER.validate_json(raw_text)
    except ValidationError:
        return None


def _v7_authored_texts(output: V7WriterOutput) -> list[str]:
    texts = [output.headline, output.summary]
    for section in output.sections:
        texts.append(section.title)
        if section.content is not None:
            texts.append(section.content)
        texts.extend(section.items)
    return texts


def validate_v7_writer_output(
    output: V7WriterOutput,
    inputs: V7WriterInputs,
) -> SafetyFilterResult:
    """Block shape, ref, source-parent, and active product-language failures.

    Claim-to-excerpt entailment is added by TASK-103/104 after the accepted
    context record contract exists. Ordinary style preferences intentionally
    do not fail this writer boundary.
    """
    evidence_by_ref = {item.ref: item for item in inputs.evidence}
    for section in output.sections:
        for ref in section.evidence_refs:
            if ref not in evidence_by_ref:
                return SafetyFilterResult(False, "unknown_evidence_ref", section.title)
            item = evidence_by_ref[ref]
            if item.kind == "source" and item.parent_ref not in section.evidence_refs:
                return SafetyFilterResult(False, "source_parent_ref_missing", section.title)

    for text in _v7_authored_texts(output):
        for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(False, f"banned_phrase:{phrase}")
        for phrase, pattern in zip(KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(False, f"banned_phrase:{phrase}")
        if _URL_PATTERN.search(text):
            return SafetyFilterResult(False, "writer_added_url")
    return SafetyFilterResult(True)


# --------------------------------------------------------------------------
# TASK-112 / v8 issue-centered narrative contract.
# V7 remains intact above for audit/reconstruction compatibility. V8 keeps the
# same opaque evidence records while changing the writer's organizing question
# from data categories to the reader's issue-understanding flow.
# --------------------------------------------------------------------------

V8_PROMPT_VERSION = "v8"
V8_POLICY_VERSION = "v8-issue-centered-1"
V8_INPUT_SCHEMA_VERSION = "v8-writer-input-1"
V8SectionType = Literal[
    "current_situation",
    "recent_change",
    "interpretation",
    "key_conditions",
    "what_to_watch",
    "limitations",
]

V8_SYSTEM_PROMPT = """\
당신은 일반 사용자가 복잡한 이슈의 현재 상황을 빠르게 이해하도록 돕는
한국어 이슈 브리핑 작성자입니다.

입력으로 제공되는 자료는 이슈 정의, 관찰 데이터, 공개 자료, 확인되지 않은
정보, 데이터 한계를 포함할 수 있습니다. 작성의 중심은 데이터가 아니라
이슈입니다. 사용자가 브리핑을 읽은 뒤 다음 질문에 답할 수 있도록 작성하십시오.
- 이 이슈는 무엇에 관한 것인가?
- 지금까지 확인된 상황은 무엇인가?
- 최근 무엇이 달라졌는가?
- 현재 상황을 판단할 때 가장 중요한 조건은 무엇인가?
- 앞으로 어떤 정보가 나오면 상황 판단이 달라질 수 있는가?

시장 수치나 데이터 종류를 중심으로 보고서를 구성하지 마십시오. 먼저 이슈의
현재 상황과 핵심 쟁점을 설명하고, 수치는 해당 설명을 뒷받침하는 보조 근거로
사용하십시오.

작성 원칙:
1. 제목이나 첫 문단에서 이슈의 핵심 쟁점을 먼저 설명합니다.
2. 시장 수치나 지표부터 시작하지 않습니다.
3. 수치는 이슈의 현재 분위기나 변화 정도를 설명하는 보조 근거로만 사용합니다.
4. 데이터 종류별로 내용을 나열하지 말고 하나의 자연스러운 이야기로 연결합니다.
5. 같은 의미의 주의 문구와 데이터 한계를 여러 섹션에서 반복하지 않습니다.
6. 현재 수치를 공식 결정, 실제 사건의 결과 또는 미래 가능성과 동일시하지 않습니다.
7. 관찰된 변화와 그 변화의 배경을 구분합니다.
8. 배경이 확인되지 않으면 "제공된 자료만으로는 변화의 배경을 확인하기 어렵습니다"라고
   표현하고 추측하지 않습니다.
9. 외부 공개 자료가 제공된 경우에만 현재 상황과 연결하여 설명합니다.
10. 제공되지 않은 사실, 인물, 날짜, 수치, 사건, 관계, 배경 또는 결과를 만들지 않습니다.
11. 근거가 부족한 섹션은 억지로 작성하지 말고 생략합니다.
12. 일반 독자가 이해하기 쉬운 자연스럽고 간결한 한국어를 사용합니다.
13. 내부 데이터 구조나 evidence, metric, ref 같은 구현 용어를 노출하지 않습니다.
14. 같은 내용을 다른 표현으로 반복하지 않습니다.

headline은 이슈의 현재 상태가 드러나는 짧은 제목으로 작성합니다. summary는
이슈가 무엇인지, 현재 어떤 상황인지, 최근 관찰된 변화가 무엇인지를 2~4문장으로
설명합니다. sections에는 입력 근거에 따라 필요한 섹션만 작성합니다. 섹션마다
핵심 메시지를 먼저 제시하고 데이터는 뒤에서 뒷받침합니다. limitations는 전체
해석에 반드시 필요한 중요한 한계가 있을 때만 한 번 작성합니다.

지정된 JSON 구조만 반환하고 추가 필드를 만들지 마십시오. 두 개에서 여섯 개의
섹션을 반환하십시오. 각 섹션은 허용된 유형 하나, 자연스러운 한국어 제목,
paragraph 또는 bullets 형식, 그리고 해당 섹션 전체를 뒷받침하는 고유한 근거
참조를 포함해야 합니다. 모든 문장에 참조를 붙이지 말고 섹션 단위로 연결합니다.

입력에 제공된 정확한 근거 참조만 사용하십시오. source:* 참조를 사용하면 같은
섹션에 그 출처의 context:* 상위 참조도 포함하십시오. 제목, 요약, 섹션 제목,
문단 또는 항목에 URL을 쓰지 마십시오. 출처 링크는 애플리케이션이 별도로 붙입니다.

작성 텍스트에는 프로젝트의 금칙 표현을 사용하지 마십시오. 사실, 출처, 참조,
관계 또는 미래 결과를 만들어내지 마십시오. 독자에게 금융 또는 시장 행동을
유도하지 마십시오. 입력 출처가 더 강한 관계를 명시적으로 뒷받침하지 않는 한
관찰 시점의 겹침은 시점의 겹침으로만 다루십시오.
"""


class V8WriterInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    category: str = Field(min_length=1, max_length=120)
    evidence: list[V7EvidenceItem] = Field(min_length=2, max_length=60)

    @model_validator(mode="after")
    def validate_evidence_bundle(self) -> "V8WriterInputs":
        refs = [item.ref for item in self.evidence]
        if len(refs) != len(set(refs)):
            raise ValueError("V8 writer evidence refs must be unique")
        ref_set = set(refs)
        if not any(item.kind == "market_definition" for item in self.evidence):
            raise ValueError("V8 writer inputs require market definition evidence")
        if not any(item.kind == "metric" for item in self.evidence):
            raise ValueError("V8 writer inputs require metric evidence")
        if any(item.parent_ref not in ref_set for item in self.evidence if item.parent_ref):
            raise ValueError("V8 source parent ref must exist in the same input bundle")
        return self


class V8WriterSection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: V8SectionType
    title: str = Field(min_length=2, max_length=100)
    format: Literal["paragraph", "bullets"]
    content: str | None = Field(default=None, min_length=30, max_length=1800)
    items: list[str] = Field(default_factory=list, max_length=8)
    evidence_refs: list[str] = Field(min_length=1, max_length=12)

    @field_validator("items")
    @classmethod
    def validate_item_bounds(cls, values: list[str]) -> list[str]:
        if any(not 15 <= len(value.strip()) <= 500 for value in values):
            raise ValueError("V8 bullet items must be 15-500 characters")
        return values

    @model_validator(mode="after")
    def validate_format_shape(self) -> "V8WriterSection":
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("V8 section evidence refs must be unique")
        if self.format == "paragraph" and (self.content is None or self.items):
            raise ValueError("V8 paragraph section requires content and no items")
        if self.format == "bullets" and (self.content is not None or not self.items):
            raise ValueError("V8 bullet section requires items and null content")
        return self


class V8WriterOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str = Field(min_length=10, max_length=100)
    summary: str = Field(min_length=100, max_length=500)
    sections: list[V8WriterSection] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def validate_section_mix(self) -> "V8WriterOutput":
        types = [section.type for section in self.sections]
        if "current_situation" not in types:
            raise ValueError("V8 output requires current_situation")
        if "recent_change" not in types:
            raise ValueError("V8 output requires recent_change")
        if len(types) != len(set(types)):
            raise ValueError("V8 section types must be unique")
        return self


_V8_WRITER_ADAPTER = TypeAdapter(V8WriterOutput)


def build_v8_prompt(inputs: V8WriterInputs) -> tuple[str, str]:
    """Build the approved issue-centered prompt over the existing evidence bundle."""
    payload = {
        "policy_version": V8_POLICY_VERSION,
        "input_schema_version": V8_INPUT_SCHEMA_VERSION,
        "issue": {
            "id": str(inputs.issue_id),
            "title": inputs.title,
            "category": inputs.category,
        },
        "writing_goal": {
            "primary_question": "현재 이 이슈는 어떤 상황이며, 앞으로 무엇을 확인해야 하는가?",
            "audience": "관련 배경지식이 많지 않은 일반 사용자",
            "tone": "중립적이고 설명적인 이슈 브리핑",
        },
        "preferred_narrative_order": [
            "이슈의 핵심 쟁점",
            "현재까지 확인된 상황",
            "최근 관찰된 변화",
            "현재 자료가 의미하는 범위",
            "향후 판단을 바꿀 핵심 조건",
        ],
        "allowed_section_types": list(V8SectionType.__args__),
        "required_output_shape": {
            "headline": "10-100 character string",
            "summary": "100-500 character string",
            "sections": [
                {
                    "type": "one allowed section type",
                    "title": "natural Korean section title",
                    "format": "paragraph or bullets",
                    "content": "paragraph text or null",
                    "items": ["bullet text; empty for paragraph"],
                    "evidence_refs": ["exact supplied ref"],
                }
            ],
        },
        "evidence": [item.model_dump(mode="json") for item in inputs.evidence],
    }
    return V8_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_v8_writer_output(raw_text: str) -> V8WriterOutput | None:
    try:
        return _V8_WRITER_ADAPTER.validate_json(raw_text)
    except ValidationError:
        return None


def validate_v8_writer_output(
    output: V8WriterOutput,
    inputs: V8WriterInputs,
) -> SafetyFilterResult:
    """Apply the retained evidence, source-parent, link, and wording blockers."""
    evidence_by_ref = {item.ref: item for item in inputs.evidence}
    for section in output.sections:
        for ref in section.evidence_refs:
            if ref not in evidence_by_ref:
                return SafetyFilterResult(False, "unknown_evidence_ref", section.title)
            item = evidence_by_ref[ref]
            if item.kind == "source" and item.parent_ref not in section.evidence_refs:
                return SafetyFilterResult(False, "source_parent_ref_missing", section.title)

    texts = [output.headline, output.summary]
    for section in output.sections:
        texts.extend([section.title, *(section.items)])
        if section.content is not None:
            texts.append(section.content)
    for text in texts:
        for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(False, f"banned_phrase:{phrase}")
        for phrase, pattern in zip(KOREAN_BANNED_SUBSTRINGS, _KOREAN_PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(False, f"banned_phrase:{phrase}")
        if _URL_PATTERN.search(text):
            return SafetyFilterResult(False, "writer_added_url")
    return SafetyFilterResult(True)
