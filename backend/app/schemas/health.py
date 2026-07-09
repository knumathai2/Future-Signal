"""Response schema for GET /api/health."""
from datetime import datetime, timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["outlook-signals-api"])
    time: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Server time the health check was evaluated, UTC.",
    )
