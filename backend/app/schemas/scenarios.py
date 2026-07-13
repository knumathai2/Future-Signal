"""Strict public schemas for the disabled-by-default scenario API."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScenarioSessionCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    session_capability: str = Field(min_length=40, max_length=80)
    issue_id: UUID
    created_at: datetime
    expires_at: datetime
    max_turns: Literal[8]
    policy_version: str
    data_as_of: datetime
    caution_note: str = Field(min_length=20, max_length=900)


class ScenarioTurnOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_id: UUID
    sequence: int = Field(ge=1)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2500)
    created_at: datetime


class ScenarioPremiseOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    premise_id: UUID
    premise_class: Literal[
        "confirmed_fact",
        "stored_observation",
        "user_assumption",
        "model_scenario",
        "unverified_context",
    ]
    text: str = Field(min_length=1, max_length=2000)
    origin_turn_id: UUID


class ScenarioSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    issue_id: UUID
    created_at: datetime
    expires_at: datetime
    max_turns: Literal[8]
    remaining_turns: int = Field(ge=0, le=8)
    policy_version: str
    data_as_of: datetime
    caution_note: str = Field(min_length=20, max_length=900)
    turns: list[ScenarioTurnOut]
    premises: list[ScenarioPremiseOut]


class ScenarioTurnCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # The service enforces the approved 1,000-character ceiling so oversized
    # requests receive the contract's safe HTTP 413 response rather than a
    # generic schema error.
    message: str = Field(strict=True, min_length=1)


class ScenarioTurnCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_id: UUID
    sequence: int = Field(ge=1)
    status: Literal["queued"]
    created: bool
    requested_at: datetime
    stream_path: str


class ScenarioTurnStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_id: UUID
    sequence: int = Field(ge=1)
    state: Literal["queued", "running", "succeeded", "failed"]
    attempt_number: int = Field(ge=0)
    requested_at: datetime
    updated_at: datetime
    assistant_turn_id: UUID | None = None
    error_code: str | None = None
