"""FastAPI application entrypoint.

Key architectural rule (ADR-051): this API reads issue data and may append a
generation request/event. It never calls Polymarket or an AI provider directly.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import categories, health, issues
from app.core.config import settings

app = FastAPI(
    title="Outlook Signals API",
    description=(
        "Read-only API for issue-change signals derived from public " "prediction-market data."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(issues.router)
app.include_router(categories.router)
