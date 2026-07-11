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
    basis: Literal["market_definition", "observed_data", "verified_context", "data_limitation"]


class BriefingItemOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(strict=True, min_length=2, max_length=120)
    explanation: str = Field(strict=True, min_length=20, max_length=700)
    basis: Literal["market_definition", "observed_data", "verified_context", "data_limitation"]


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


class V6MarketDefinitionBlockOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(strict=True, min_length=30, max_length=900)
    basis: Literal["market_definition"]


class V6GeneralBlockOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(strict=True, min_length=30, max_length=900)
    basis: Literal["general_scenario"]


class V6VerifiedBlockOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(strict=True, min_length=30, max_length=1200)
    basis: Literal["verified_context"]
    candidate_ids: list[UUID] = Field(min_length=1, max_length=3)


class V6GeneralScenarioOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(strict=True, min_length=2, max_length=100)
    text: str = Field(strict=True, min_length=30, max_length=900)
    basis: Literal["general_scenario"]


class V6VerifiedInterpretationOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(strict=True, min_length=2, max_length=100)
    text: str = Field(strict=True, min_length=30, max_length=900)
    basis: Literal["verified_context"]
    candidate_ids: list[UUID] = Field(min_length=1, max_length=3)


class V6MaterialToCheckOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scenario_index: int = Field(ge=1, le=4)
    title: str = Field(strict=True, min_length=2, max_length=120)
    text: str = Field(strict=True, min_length=20, max_length=700)
    basis: Literal["general_scenario"]


class V6ChangeWithEvidenceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["change_with_evidence"]
    verified_background: V6VerifiedBlockOut
    conditional_interpretations: list[V6VerifiedInterpretationOut] = Field(
        min_length=1, max_length=4
    )


class V6ChangeWithoutEvidenceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["change_without_evidence"]
    conditional_scenarios: list[V6GeneralScenarioOut] = Field(min_length=1, max_length=4)
    materials_to_check: list[V6MaterialToCheckOut] = Field(min_length=1, max_length=8)


class V6StableWithEvidenceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["stable_with_evidence"]
    issue_explanation: V6MarketDefinitionBlockOut
    verified_background: V6VerifiedBlockOut
    conditional_scenarios: list[V6GeneralScenarioOut] = Field(min_length=1, max_length=4)


class V6StableWithoutEvidenceOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["stable_without_evidence"]
    issue_explanation: V6GeneralBlockOut
    conditional_scenarios: list[V6GeneralScenarioOut] = Field(min_length=1, max_length=4)
    materials_to_check: list[V6MaterialToCheckOut] = Field(min_length=1, max_length=8)


V6BriefingOut = Annotated[
    V6ChangeWithEvidenceOut
    | V6ChangeWithoutEvidenceOut
    | V6StableWithEvidenceOut
    | V6StableWithoutEvidenceOut,
    Field(discriminator="mode"),
]


class V6ObservedChangeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: int
    window: Literal["24h"]
    current_value: float = Field(ge=0, le=1)
    change_value: float | None
    significant: bool
    threshold: float = Field(ge=0, le=1)


class V6ResolutionReferenceOut(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["available", "unavailable"]
    condition_text: str | None
    deadline: datetime | None
    exclusions: list[str]
    source_url: str | None

    @model_validator(mode="after")
    def validate_availability(self) -> "V6ResolutionReferenceOut":
        if self.status == "available" and not self.condition_text:
            raise ValueError("Available resolution reference requires condition text")
        if self.status == "unavailable" and any(
            (
                self.condition_text,
                self.deadline,
                self.exclusions,
                self.source_url,
            )
        ):
            raise ValueError("Unavailable resolution reference cannot expose rule fields")
        if self.source_url is not None:
            parsed = urlparse(self.source_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("Resolution source URL must be absolute HTTP(S)")
        return self


class IssueReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    generated_at: datetime
    data_as_of: datetime
    episode_at: datetime
    report_mode: Literal[
        "change_with_evidence",
        "change_without_evidence",
        "stable_with_evidence",
        "stable_without_evidence",
    ]
    observed_change: V6ObservedChangeOut
    briefing: V6BriefingOut
    resolution_reference: V6ResolutionReferenceOut
    evidence_refs: list[str] = Field(min_length=1, max_length=4)
    context_candidates: list[ContextCandidateOut] = Field(max_length=3)
    relationship_boundary: str = Field(strict=True, min_length=50, max_length=500)
    data_limitations: str = Field(strict=True, min_length=50, max_length=900)
    caution_note: str = Field(strict=True, min_length=120, max_length=700)
    status: Literal["success"]
    report_version: Literal["v6"]

    @model_validator(mode="after")
    def validate_evidence_shape(self) -> "IssueReportResponse":
        candidate_refs = [f"candidate:{candidate.id}" for candidate in self.context_candidates]
        if not self.evidence_refs[0].startswith("metric:"):
            raise ValueError("The first v6 evidence reference must identify a metric")
        if self.evidence_refs[1:] != candidate_refs:
            raise ValueError("Candidate evidence references must match public candidates")
        if self.report_mode != self.briefing.mode:
            raise ValueError("Report mode must match the discriminated briefing mode")
        has_evidence = self.report_mode.endswith("with_evidence")
        if has_evidence != bool(self.context_candidates):
            raise ValueError("Report mode evidence state must match public candidates")
        has_change = self.report_mode.startswith("change_")
        if has_change != self.observed_change.significant:
            raise ValueError("Report mode change state must match observed change")
        if self.evidence_refs[0] != f"metric:{self.observed_change.metric_id}":
            raise ValueError("Observed metric ID must match the first evidence reference")
        if self.data_as_of > self.generated_at or self.episode_at > self.generated_at:
            raise ValueError("V6 report timestamps cannot be later than generation")
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
