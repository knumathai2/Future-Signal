"""Uptime/monitoring check. No DB access, no secrets or deployment internals."""
from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return a stable status payload confirming the API process is up."""
    return HealthResponse(status="ok", service="outlook-signals-api")
