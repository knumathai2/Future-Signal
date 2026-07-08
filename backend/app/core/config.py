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


settings = Settings()
