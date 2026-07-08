"""Response schema for GET /api/health."""
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["outlook-signals-api"])
    time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server time the health check was evaluated, UTC.",
    )
