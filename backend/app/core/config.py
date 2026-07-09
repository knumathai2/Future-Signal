"""Application configuration loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-4o-mini"


def _is_openrouter_key(api_key: str | None) -> bool:
    return bool(api_key and api_key.startswith("sk-or-"))


def _resolve_ai_provider(
    provider: str | None,
    openrouter_api_key: str | None,
    openai_api_key: str | None,
) -> str:
    if provider:
        normalized = provider.strip().lower()
        if normalized in {"openai", "openrouter"}:
            return normalized
    if openrouter_api_key or _is_openrouter_key(openai_api_key):
        return "openrouter"
    return "openai"


def _resolve_ai_model(provider: str, raw_model: str | None) -> str:
    model = (raw_model or "").strip()
    if not model:
        return OPENROUTER_DEFAULT_MODEL if provider == "openrouter" else OPENAI_DEFAULT_MODEL
    if provider == "openrouter" and "/" not in model and not model.startswith("~"):
        return f"openai/{model}"
    return model


def _resolve_ai_base_url(provider: str, raw_base_url: str | None) -> str | None:
    base_url = (raw_base_url or "").strip()
    if base_url:
        return base_url
    if provider == "openrouter":
        return OPENROUTER_BASE_URL
    return None


class Settings:
    def __init__(self) -> None:
        self.env: str = os.getenv("ENV", "local")
        self.database_url: str | None = os.getenv("DATABASE_URL")
        # Comma-separated list; always includes localhost dev ports per standards.md CORS rule.
        self.cors_origins: list[str] = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if origin.strip()
        ]
        # TASK-015/TASK-042: report generation uses an OpenAI-compatible chat
        # client. OpenRouter is supported without adding a dependency by
        # pointing the existing OpenAI SDK at OpenRouter's compatible endpoint.
        self.openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
        self.ai_provider: str = _resolve_ai_provider(
            os.getenv("AI_PROVIDER"),
            self.openrouter_api_key,
            self.openai_api_key,
        )
        self.ai_api_key: str | None = (
            self.openrouter_api_key if self.ai_provider == "openrouter" else None
        ) or self.openai_api_key
        self.openai_model: str = _resolve_ai_model(
            self.ai_provider,
            os.getenv("OPENAI_MODEL"),
        )
        self.ai_base_url: str | None = _resolve_ai_base_url(
            self.ai_provider,
            os.getenv("OPENAI_BASE_URL"),
        )
        self.openrouter_http_referer: str | None = os.getenv("OPENROUTER_HTTP_REFERER")
        self.openrouter_app_title: str | None = os.getenv(
            "OPENROUTER_APP_TITLE", "Outlook Signals"
        )


settings = Settings()
