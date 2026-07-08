"""FastAPI application entrypoint.

Key architectural rule (Technical Design §3): this API layer reads from
Postgres only. It must never call the Polymarket or AI provider APIs
directly - that is the batch collector's job.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import settings

app = FastAPI(
    title="Outlook Signals API",
    description="Read-only API for issue-change signals derived from public prediction-market data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
