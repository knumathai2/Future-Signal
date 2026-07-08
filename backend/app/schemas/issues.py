"""Response schemas for the read-only issues/signals/reports/categories API.

Field names mirror the example JSON already agreed in
../../docs/tech-design/03-api-and-batch-pipeline.md §5 - this module is the
executable draft of that contract, not a new design.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal[
    "sufficient",
    "caution_low_activity",
    "caution_high_volatility",
    "insufficient_data",
]
SignalSeverity = Literal["low", "medium", "high", "critical"]
IssueStatus = Literal["active", "closed", "resolved"]


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
    """Fixed template slots only - never free-form (ADR-003)."""

    issue_summary: str
    movement_explanation: str
    key_change_context: str
    uncertainty_summary: str
    neutral_conclusion: str


class IssueReportResponse(BaseModel):
    id: str
    generated_at: datetime
    data_as_of: datetime
    content: ReportContent
    status: Literal["success"]


class ReportNotYetGenerated(BaseModel):
    status: Literal["not_yet_generated"]


class CategoryListResponse(BaseModel):
    categories: list[str]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
