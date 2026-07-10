"""Response schemas for the read-only issues/signals/reports/categories API.

Field names mirror the example JSON already agreed in
../../docs/tech-design/03-api-and-batch-pipeline.md §5 - this module is the
executable draft of that contract, not a new design.
"""
import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ConfidenceLevel = Literal[
    "sufficient",
    "caution_low_activity",
    "caution_high_volatility",
    "insufficient_data",
]
SignalSeverity = Literal["low", "medium", "high", "critical"]
IssueStatus = Literal["active", "closed", "resolved"]

_SENTENCE_TERMINATOR_PATTERN = re.compile(r"[.!?]+(?=\s|$)")


def _sentence_count(value: str) -> int:
    matches = _SENTENCE_TERMINATOR_PATTERN.findall(value.strip())
    return len(matches) or 1


class IssueSummary(BaseModel):
    id: str
    title: str
    category: str
    current_value: float = Field(description="Reflected expectation value, 0-1.")
    change_24h: float | None
    change_7d: float | None
    confidence_level: ConfidenceLevel
    heat_score: float | None


class IssueListResponse(BaseModel):
    data_as_of: datetime
    issues: list[IssueSummary]


class RelatedEventCandidate(BaseModel):
    """Always a candidate for context - never asserted as a cause (glossary.md)."""

    event_title: str
    event_date: datetime
    note: str


class SignalOut(BaseModel):
    signal_type: Literal["expectation_shift"]
    severity: SignalSeverity
    window: str
    magnitude: float
    triggered_at: datetime


class IssueDetail(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: IssueStatus
    outcome_label: str
    current_value: float
    change_24h: float | None
    change_7d: float | None
    confidence_level: ConfidenceLevel
    heat_score: float | None
    data_as_of: datetime
    related_events: list[RelatedEventCandidate]
    signals: list[SignalOut]


class HistoryPoint(BaseModel):
    captured_at: datetime
    value: float


class IssueHistoryResponse(BaseModel):
    data_as_of: datetime
    window: Literal["24h", "7d", "30d"]
    points: list[HistoryPoint]


class ReportContent(BaseModel):
    """Fixed template slots only - never free-form (ADR-003 / ADR-033).

    `extra="forbid"` is load-bearing: the LLM response must
    parse into exactly these 8 fields, nothing more/fewer - a response with
    an extra field fails validation and is treated as a malformed-schema
    failure, not silently trimmed.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    issue_overview: Annotated[
        str,
        Field(
            strict=True,
            min_length=30,
            max_length=600,
            description="What the issue is and the condition being tracked.",
        ),
    ]
    current_data_reading: Annotated[
        str,
        Field(
            strict=True,
            min_length=50,
            max_length=700,
            description="Values and movement currently observed in public data.",
        ),
    ]
    possible_outlook: Annotated[
        str,
        Field(
            strict=True,
            min_length=60,
            max_length=700,
            description="Conditional developments without a real-world forecast.",
        ),
    ]
    possible_drivers: Annotated[
        str,
        Field(
            strict=True,
            min_length=80,
            max_length=700,
            description="Reviewed context candidates to compare without causation.",
        ),
    ]
    external_context: Annotated[
        str | None,
        Field(
            strict=True,
            min_length=40,
            max_length=700,
            description="Manually reviewed external context narrative.",
        ),
    ]
    what_to_check: Annotated[
        str,
        Field(
            strict=True,
            min_length=30,
            max_length=600,
            description="Facts, dates, criteria, and sources needing verification.",
        ),
    ]
    data_limitations: Annotated[
        str,
        Field(
            strict=True,
            min_length=80,
            max_length=700,
            description="Activity, volatility, history, and representativeness limits.",
        ),
    ]
    caution_note: Annotated[
        str,
        Field(
            strict=True,
            min_length=120,
            max_length=700,
            description="Mandatory report-level interpretation caution.",
        ),
    ]

    @field_validator("*")
    @classmethod
    def limit_sentence_count(cls, value: str | None) -> str | None:
        """Reject stored content outside ADR-033's 1-5 sentence limit."""
        if value is not None and _sentence_count(value) > 5:
            raise ValueError("Report fields must contain at most five sentences.")
        return value


class IssueReportResponse(BaseModel):
    id: str
    generated_at: datetime
    data_as_of: datetime
    content: ReportContent
    status: Literal["success"]
    report_version: Literal["v3"]


class ReportNotYetGenerated(BaseModel):
    status: Literal["not_yet_generated"]


class CategoryListResponse(BaseModel):
    categories: list[str]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class ReportContentV2(BaseModel):
    """Legacy v2 template slots, kept for compatibility with the generator

    (TASK-049 separately owns updates to the generator, prompt version, etc.)
    """

    model_config = ConfigDict(extra="forbid")

    issue_explainer: str
    why_it_matters: str
    current_reading: str
    scenario_major_change: str
    scenario_limited_change: str
    scenario_status_quo: str
    check_points: str
    caution_note: str
