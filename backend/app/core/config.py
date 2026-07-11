"""Application configuration loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-4o-mini"
CONTEXT_MAX_SEARCH_QUERIES = 6
CONTEXT_MAX_SEARCH_RESULTS = 30
CONTEXT_MAX_RESULTS_PER_QUERY = 5


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


def _bounded_int(raw_value: str | None, *, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(raw_value) if raw_value is not None else default
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def _bounded_float(
    raw_value: str | None, *, default: float, minimum: float, maximum: float
) -> float:
    try:
        value = float(raw_value) if raw_value is not None else default
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


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
        # TASK-058: bounded OpenRouter server-tool research. These limits are
        # clamped at the ADR-038/TASK-055 maxima even if environment values are
        # larger, so configuration cannot silently expand paid research scope.
        self.context_research_model: str = _resolve_ai_model(
            "openrouter",
            os.getenv("CONTEXT_RESEARCH_MODEL") or self.openai_model,
        )
        self.context_verifier_model: str = os.getenv("CONTEXT_VERIFIER_MODEL", "").strip()
        raw_engine = os.getenv("CONTEXT_SEARCH_ENGINE", "auto").strip().lower()
        self.context_search_engine: str = (
            raw_engine
            if raw_engine in {"auto", "native", "exa", "firecrawl", "parallel", "perplexity"}
            else "auto"
        )
        self.context_max_search_queries: int = _bounded_int(
            os.getenv("CONTEXT_MAX_SEARCH_QUERIES"),
            default=CONTEXT_MAX_SEARCH_QUERIES,
            minimum=1,
            maximum=CONTEXT_MAX_SEARCH_QUERIES,
        )
        self.context_max_search_results: int = _bounded_int(
            os.getenv("CONTEXT_MAX_SEARCH_RESULTS"),
            default=CONTEXT_MAX_SEARCH_RESULTS,
            minimum=1,
            maximum=CONTEXT_MAX_SEARCH_RESULTS,
        )
        self.context_max_results_per_query: int = _bounded_int(
            os.getenv("CONTEXT_MAX_RESULTS_PER_QUERY"),
            default=CONTEXT_MAX_RESULTS_PER_QUERY,
            minimum=1,
            maximum=25,
        )
        self.context_change_threshold: float = _bounded_float(
            os.getenv("CONTEXT_CHANGE_THRESHOLD"),
            default=0.05,
            minimum=0.0,
            maximum=1.0,
        )
        self.context_staleness_hours: int = _bounded_int(
            os.getenv("CONTEXT_STALENESS_HOURS"),
            default=24,
            minimum=1,
            maximum=168,
        )
        self.context_budget_usd: float = _bounded_float(
            os.getenv("CONTEXT_BUDGET_USD"),
            default=100.0,
            minimum=0.0,
            maximum=100.0,
        )
        self.context_cost_reservation_usd: float = _bounded_float(
            os.getenv("CONTEXT_COST_RESERVATION_USD"),
            default=2.0,
            minimum=0.01,
            maximum=100.0,
        )


settings = Settings()
