"""Response schema for GET /api/health."""
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["outlook-signals-api"])
    time: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Server time the health check was evaluated, UTC.",
    )
