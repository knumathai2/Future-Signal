"""AI report generation (TASK-015): fixed-template prompt, LLM call, strict
schema parse, and the banned-phrase/pattern safety filter.

Scope note: this module produces a `ReportContent` (or a documented failure)
for exactly one market. It does not decide *which* markets to regenerate or
touch `ai_reports`/`data_collection_logs` directly - that orchestration
(regeneration eligibility, top-10 cap, storage, audit logging) is
`app/core/ai_report_batch.py`. Keeping the boundary here means the prompt/
parse/filter logic can be unit-tested with a fake `LLMClient` and no
database at all.

Technical Design §9-10 is the binding spec; nothing here may add a free-text
insertion point beyond the named slots in `USER_PROMPT_TEMPLATE`, and nothing
here may call a paid provider except through `LLMClient.complete()`, which
callers construct explicitly (see `OpenAICompatibleReportClient`) - importing this
module never triggers a network call or requires an API key.

AI provider: OpenAI-compatible chat completions, with OpenRouter selected when
configured, per human-approved ADRs in memory/decisions.md.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from app.schemas.issues import ReportContent

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v2"

# --------------------------------------------------------------------------
# 10.1 System prompt (fixed, never modified per-request)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are generating a concise, neutral issue explainer for a public
issue-monitoring dashboard. Write in clear Korean for non-specialist readers.
You are explaining the market question and the public data context, not
predicting real-world outcomes and not giving advice of any kind.

Rules you must always follow:
- Explain the issue in plain language before mentioning the data reading.
- Use scenario sections only as conditional explanations of what the market
  question would mean if that condition is confirmed, limited, or not confirmed.
- Never label a scenario as best, worst, good, bad, desirable, or undesirable.
- Never state or imply that an outcome will or will not happen.
- Never use: bet, buy, sell, trade, position, long, short, profit, win rate,
  recommend, guaranteed, best pick, follow, copy, opportunity.
- Never suggest any action the reader should take.
- Never use causal connectors such as "because", "due to", or "caused by".
- If a related event candidate is provided, describe it only as a "candidate
  for context," never as a cause.
- If data is limited (low volume, limited history, high volatility), say so
  plainly instead of writing around it.
- Keep every section to 1-3 sentences."""

# --------------------------------------------------------------------------
# 10.2 User/task prompt template (fixed - the only variation between calls is
# filling these named slots, never additional free text)
# --------------------------------------------------------------------------
USER_PROMPT_TEMPLATE = """\
Market title: {title}
Market description: {description}
Category: {category}
Current expectation value: {current_value}
24h change: {change_24h}
7d change: {change_7d}
Data reliability/caution level: {confidence_level}
Recent inflection point (if any): {inflection_point_summary}
Related event candidate (if any): {related_event_or_none}

Produce a JSON object in Korean with exactly these fields:
{{
  "issue_explainer": "...",
  "why_it_matters": "...",
  "current_reading": "...",
  "scenario_major_change": "...",
  "scenario_limited_change": "...",
  "scenario_status_quo": "...",
  "check_points": "...",
  "caution_note": "..."
}}"""


@dataclass
class ReportPromptInputs:
    """Structured, already-computed inputs only - never raw free text from a
    user or an unvetted source. Every field maps 1:1 to a
    `USER_PROMPT_TEMPLATE` slot."""

    title: str
    description: str
    category: str
    current_value: float
    change_24h: float | None
    change_7d: float | None
    confidence_level: str
    inflection_point_summary: str | None
    related_event_or_none: str | None


def _format_pp(change: float | None) -> str:
    """`change_24h`/`change_7d` are raw 0-1 deltas (Technical Design §7) -
    render as percentage points, or an explicit not-available string rather
    than fabricating 0 (no-fabrication rule, AGENTS.md)."""
    if change is None:
        return "not available (insufficient history)"
    return f"{change * 100:+.1f}pp"


def build_prompt(inputs: ReportPromptInputs) -> tuple[str, str]:
    """Returns `(system_prompt, user_prompt)`. `SYSTEM_PROMPT` is returned
    verbatim; `user_prompt` is `USER_PROMPT_TEMPLATE` with only the named
    slots filled from `inputs` - no other text is ever inserted."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=inputs.title,
        description=inputs.description,
        category=inputs.category,
        current_value=f"{inputs.current_value * 100:.1f}%",
        change_24h=_format_pp(inputs.change_24h),
        change_7d=_format_pp(inputs.change_7d),
        confidence_level=inputs.confidence_level,
        inflection_point_summary=inputs.inflection_point_summary or "None",
        related_event_or_none=inputs.related_event_or_none or "None",
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
# Strict schema parse (Technical Design §10.6: malformed JSON, or JSON that
# doesn't match the 5-field schema exactly, is a failure - never partially
# parsed).
# --------------------------------------------------------------------------


def parse_report_content(raw_text: str) -> ReportContent | None:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        # ReportContent has extra="forbid" (app/schemas/issues.py) - an extra
        # or missing field fails validation here rather than being trimmed.
        return ReportContent.model_validate(payload)
    except ValidationError:
        return None


# --------------------------------------------------------------------------
# 10.4 Safety filter - runs after every generation, before storage.
# --------------------------------------------------------------------------

# Union of standards.md's Content Safety Lint prohibited list, UX Design
# §5.3, memory/glossary.md's wording policy, and the system prompt's own
# never-use list. Single words are matched on word boundaries so e.g. "long"
# doesn't also reject "belong"; multi-word phrases match as a unit.
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

# Structural rules (standards.md Content Safety Lint + Technical Design
# §10.4): causal language and action-suggesting phrasing, independent of the
# single-word list above.
BANNED_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bwill (happen|occur)\b",
        r"\byou should\b",
        r"\bbecause\b",
        r"\bdue to\b",
        r"\bcaused by\b",
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

REPORT_FIELDS: tuple[str, ...] = (
    "issue_explainer",
    "why_it_matters",
    "current_reading",
    "scenario_major_change",
    "scenario_limited_change",
    "scenario_status_quo",
    "check_points",
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
    against the banned-phrase list, then the banned-pattern list."""
    for field in REPORT_FIELDS:
        text = getattr(content, field)
        for phrase, pattern in zip(BANNED_PHRASES, _PHRASE_PATTERNS, strict=True):
            if pattern.search(text):
                return SafetyFilterResult(passed=False, rule=f"banned_phrase:{phrase}", field=field)
        for pattern in BANNED_PATTERNS:
            if pattern.search(text):
                return SafetyFilterResult(
                    passed=False, rule=f"banned_pattern:{pattern.pattern}", field=field
                )
    return SafetyFilterResult(passed=True)
