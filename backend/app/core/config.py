"""Application configuration loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    env: str = os.getenv("ENV", "local")
    database_url: str | None = os.getenv("DATABASE_URL")
    # Comma-separated list; always includes localhost dev ports per standards.md CORS rule.
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]
    # TASK-015 (data-ai/TASK-015-template-report-generation): AI provider selection
    # is OpenAI per ADR (memory/decisions.md), human-approved. No key = no live
    # calls; app/core/ai_report.py callers must check this before constructing
    # OpenAIReportClient.
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
