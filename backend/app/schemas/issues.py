"""Response schemas for the read-only issues/signals/reports/categories API.

Field names mirror the example JSON already agreed in
../../docs/tech-design/03-api-and-batch-pipeline.md §5 - this module is the
executable draft of that contract, not a new design.
"""

import re
from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class ConditionalScenarioOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(strict=True, min_length=2, max_length=100)
    narrative: str = Field(strict=True, min_length=30, max_length=900)
    basis: Literal[
        "market_definition", "observed_data", "verified_context", "data_limitation"
    ]


class BriefingItemOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(strict=True, min_length=2, max_length=120)
    explanation: str = Field(strict=True, min_length=20, max_length=700)
    basis: Literal[
        "market_definition", "observed_data", "verified_context", "data_limitation"
    ]


class ReportContent(BaseModel):
    """Strict public v5 content (ADR-048)."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    executive_summary: Annotated[str, Field(strict=True, min_length=80, max_length=1200)]
    current_data_interpretation: Annotated[str, Field(strict=True, min_length=50, max_length=1200)]
    conditional_scenarios: list[ConditionalScenarioOut] = Field(min_length=1, max_length=4)
    factors_to_check: list[BriefingItemOut] = Field(min_length=2, max_length=6)
    signals_to_watch: list[BriefingItemOut] = Field(min_length=2, max_length=6)
    evidence_synthesis: Annotated[
        str | None,
        Field(default=..., strict=True, min_length=50, max_length=1800),
    ]
    relationship_boundary: Annotated[str, Field(strict=True, min_length=50, max_length=500)]
    data_limitations: Annotated[
        str,
        Field(
            strict=True,
            min_length=50,
            max_length=900,
        ),
    ]
    caution_note: Annotated[
        str,
        Field(
            strict=True,
            min_length=120,
            max_length=700,
        ),
    ]

    @field_validator(
        "executive_summary",
        "current_data_interpretation",
        "evidence_synthesis",
        "relationship_boundary",
        "data_limitations",
        "caution_note",
    )
    @classmethod
    def limit_sentence_count(cls, value: str | None) -> str | None:
        """Reject stored prose outside the v5 one-to-five sentence limit."""
        if value is not None and _sentence_count(value) > 5:
            raise ValueError("Report fields must contain at most five sentences.")
        return value


class ContextSourceOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(strict=True, min_length=1)
    url: str = Field(strict=True, min_length=1)
    domain: str = Field(strict=True, min_length=1)
    published_at: datetime | None
    source_type: Literal["official", "independent_secondary"]

    @model_validator(mode="after")
    def validate_annotation_url(self) -> "ContextSourceOut":
        parsed = urlparse(self.url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.hostname.lower() != self.domain.lower().rstrip(".")
        ):
            raise ValueError("Public source URL and domain must match stored citation data")
        return self


class ContextCandidateOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID
    title: str = Field(strict=True, min_length=1)
    event_at: datetime
    summary: str = Field(strict=True, min_length=1)
    sources: list[ContextSourceOut] = Field(min_length=1)


class IssueReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    generated_at: datetime
    data_as_of: datetime
    episode_at: datetime
    content: ReportContent
    evidence_refs: list[str] = Field(min_length=1, max_length=4)
    context_candidates: list[ContextCandidateOut] = Field(max_length=3)
    status: Literal["success"]
    report_version: Literal["v5"]

    @model_validator(mode="after")
    def validate_evidence_shape(self) -> "IssueReportResponse":
        candidate_refs = [f"candidate:{candidate.id}" for candidate in self.context_candidates]
        if not self.evidence_refs[0].startswith("metric:"):
            raise ValueError("The first v5 evidence reference must identify a metric")
        if self.evidence_refs[1:] != candidate_refs:
            raise ValueError("Candidate evidence references must match public candidates")
        if (self.content.evidence_synthesis is None) != (not self.context_candidates):
            raise ValueError("Evidence synthesis nullability must match candidate presence")
        if self.data_as_of > self.generated_at or self.episode_at > self.generated_at:
            raise ValueError("V5 report timestamps cannot be later than generation")
        return self


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
