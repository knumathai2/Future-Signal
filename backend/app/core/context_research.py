"""Bounded OpenRouter web research for v4 context candidates (TASK-058).

Only OpenRouter API ``url_citation`` annotations become evidence. URLs written
inside model content are never parsed or trusted. This module performs no DB
write and makes no network call until ``OpenRouterContextResearchClient`` is
explicitly constructed and ``research`` is invoked.
"""

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from urllib.parse import urlparse
from uuid import UUID

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import (
    CONTEXT_MAX_RESULTS_PER_QUERY,
    CONTEXT_MAX_SEARCH_QUERIES,
    CONTEXT_MAX_SEARCH_RESULTS,
    OPENROUTER_BASE_URL,
    Settings,
)

RESEARCH_POLICY_VERSION = "v4"
RESEARCH_SYSTEM_PROMPT = """\
You research public context for an issue-monitoring dashboard. Use the provided
OpenRouter web-search server tool and only the bounded suggested queries. Return
strict JSON. Do not state that any event caused or explains a data movement.
Do not assert a real-world result. A candidate may describe only what a cited
source records and its timing relative to the supplied review window.

For every candidate, copy only URLs that appeared in the web-search results.
Never invent or repair a URL, title, date, entity, or tracked condition. If the
sources do not directly support a candidate, omit it. Return at most 30
candidates; later deterministic verification will apply a stricter gate."""


class ContextResearchError(RuntimeError):
    """Fail-closed error raised for provider, schema, or provenance failures."""


class ResearchInputs(BaseModel):
    """Structured market and episode inputs accepted by the research client."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    market_id: UUID
    episode_at: datetime
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1)
    tracked_condition: str = Field(min_length=1)
    end_date: datetime | None
    resolution_source: str | None
    current_value: float = Field(ge=0, le=1)
    change_24h: float
    change_7d: float
    inflection_at: datetime | None
    search_window_start: datetime
    search_window_end: datetime
    allowed_domains: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            domain = value.strip().lower().rstrip(".")
            if not domain or "://" in domain or "/" in domain:
                raise ValueError("allowed_domains must contain domain names only")
            if domain not in normalized:
                normalized.append(domain)
        return normalized

    @field_validator(
        "episode_at",
        "end_date",
        "inflection_at",
        "search_window_start",
        "search_window_end",
    )
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("research timestamps must include a timezone")
        return value


class NormalizedCitation(BaseModel):
    """Citation provenance derived exclusively from an API annotation."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str
    url: str
    canonical_url: str
    title: str
    domain: str
    content_excerpt: str
    content_hash: str
    retrieved_at: datetime


class _ProviderCandidate(BaseModel):
    """Strict raw model shape; URLs are mapped to annotation IDs after parse."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidate_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    event_at: datetime | None
    citation_urls: list[str] = Field(min_length=1, max_length=30)
    matched_entities: list[str] = Field(max_length=20)
    matched_condition: str = Field(min_length=1)
    temporal_relation: Literal["before_window", "same_window", "after_window"]

    @field_validator("event_at")
    @classmethod
    def require_event_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("candidate event_at must include a timezone")
        return value


class _ProviderResearchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queries: list[str] = Field(max_length=CONTEXT_MAX_SEARCH_QUERIES)
    candidates: list[_ProviderCandidate] = Field(max_length=CONTEXT_MAX_SEARCH_RESULTS)


class ResearchCandidateDraft(BaseModel):
    """Normalized research output handed to TASK-059 verification."""

    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    title: str
    event_at: datetime | None
    citation_ids: list[str]
    matched_entities: list[str]
    matched_condition: str
    temporal_relation: Literal["before_window", "same_window", "after_window"]

    @field_validator("event_at")
    @classmethod
    def require_event_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("candidate event_at must include a timezone")
        return value


class ResearchUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    web_search_requests: int = 0
    cost_usd: float | None = None


class ContextResearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    policy_version: Literal["v4"] = RESEARCH_POLICY_VERSION
    queries: list[str]
    citations: list[NormalizedCitation]
    candidates: list[ResearchCandidateDraft]
    usage: ResearchUsage


class ChatCompletionsTransport(Protocol):
    @property
    def chat(self) -> Any: ...


def build_search_queries(
    inputs: ResearchInputs, *, limit: int = CONTEXT_MAX_SEARCH_QUERIES
) -> list[str]:
    """Build a deterministic, de-duplicated query allowlist from market data."""
    start = inputs.search_window_start.date().isoformat()
    end = inputs.search_window_end.date().isoformat()
    end_date = inputs.end_date.date().isoformat() if inputs.end_date else None
    candidates = [
        f'"{inputs.title}" {start} {end}',
        f'"{inputs.title}" "{inputs.tracked_condition}"',
        f'"{inputs.description}" {inputs.category}',
        f'"{inputs.title}" official update',
        f'"{inputs.title}" {end_date}' if end_date else "",
    ]
    if inputs.resolution_source:
        resolution_domain = urlparse(inputs.resolution_source).hostname or ""
        candidates.append(f'site:{resolution_domain} "{inputs.title}"')

    queries: list[str] = []
    for query in candidates:
        normalized = " ".join(query.split())
        if normalized and normalized not in queries:
            queries.append(normalized)
        if len(queries) >= min(limit, CONTEXT_MAX_SEARCH_QUERIES):
            break
    return queries


def _build_user_prompt(inputs: ResearchInputs, queries: list[str]) -> str:
    payload = inputs.model_dump(mode="json")
    payload["suggested_queries"] = queries
    return (
        "You must execute at least one web search before answering. Research this change "
        "episode using only the suggested queries. Return JSON with "
        'exactly {"queries": [string], "candidates": [{"candidate_key": string, '
        '"title": string, "event_at": ISO-8601|null, "citation_urls": [string], '
        '"matched_entities": [string], "matched_condition": string, '
        '"temporal_relation": "before_window"|"same_window"|"after_window"}]}. '
        "The queries array must copy exact strings from suggested_queries; never "
        "rewrite, translate, or list a tool-generated variant. "
        "Every citation_urls value must exactly match a search-result URL.\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    data = getattr(value, "__dict__", None)
    return data if isinstance(data, Mapping) else {}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_citations(
    annotations: list[Any], *, retrieved_at: datetime
) -> list[NormalizedCitation]:
    citations_by_url: dict[str, NormalizedCitation] = {}
    for raw_annotation in annotations:
        annotation = _as_mapping(raw_annotation)
        if annotation.get("type") != "url_citation":
            continue
        nested = _as_mapping(annotation.get("url_citation"))
        citation = nested or annotation
        url = str(citation.get("url") or "").strip()
        title = str(citation.get("title") or "").strip()
        if not url or not title:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        excerpt = str(citation.get("content") or "").strip()
        normalized = NormalizedCitation(
            citation_id=f"citation:{_sha256(url)}",
            url=url,
            canonical_url=url,
            title=title,
            domain=parsed.hostname.lower(),
            content_excerpt=excerpt,
            content_hash=_sha256(excerpt),
            retrieved_at=retrieved_at,
        )
        existing = citations_by_url.get(url)
        if existing is None or len(normalized.content_excerpt) > len(existing.content_excerpt):
            citations_by_url[url] = normalized
    return list(citations_by_url.values())


def _parse_usage(raw_usage: Any) -> ResearchUsage:
    usage = _as_mapping(raw_usage)
    server_tool_use = _as_mapping(usage.get("server_tool_use"))
    cost = usage.get("cost")
    return ResearchUsage(
        input_tokens=int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or usage.get("output_tokens") or 0),
        web_search_requests=int(server_tool_use.get("web_search_requests") or 0),
        cost_usd=float(cost) if cost is not None else None,
    )


def _combine_usage(left: ResearchUsage, right: ResearchUsage) -> ResearchUsage:
    costs = [cost for cost in (left.cost_usd, right.cost_usd) if cost is not None]
    return ResearchUsage(
        input_tokens=left.input_tokens + right.input_tokens,
        output_tokens=left.output_tokens + right.output_tokens,
        web_search_requests=left.web_search_requests + right.web_search_requests,
        cost_usd=round(sum(costs), 8) if costs else None,
    )


class OpenRouterContextResearchClient:
    """OpenAI-SDK transport configured for OpenRouter's web-search server tool."""

    def __init__(
        self,
        client: ChatCompletionsTransport,
        model: str,
        *,
        engine: str = "auto",
        max_search_queries: int = CONTEXT_MAX_SEARCH_QUERIES,
        max_search_results: int = CONTEXT_MAX_SEARCH_RESULTS,
        max_results_per_query: int = CONTEXT_MAX_RESULTS_PER_QUERY,
        extra_headers: dict[str, str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self.model = model
        self._engine = engine
        self._max_search_queries = min(max(max_search_queries, 1), CONTEXT_MAX_SEARCH_QUERIES)
        self._max_search_results = min(max(max_search_results, 1), CONTEXT_MAX_SEARCH_RESULTS)
        self._max_results_per_query = min(max(max_results_per_query, 1), 25)
        self._extra_headers = extra_headers or {}
        self._clock = clock or (lambda: datetime.now(UTC))
        self.last_usage = ResearchUsage()

    def research(self, inputs: ResearchInputs) -> ContextResearchResult:
        accumulated = ResearchUsage()
        for attempt in range(2):
            try:
                result = self._research_once(inputs)
            except ContextResearchError:
                accumulated = _combine_usage(accumulated, self.last_usage)
                self.last_usage = accumulated
                if attempt == 1:
                    raise
                continue
            combined = _combine_usage(accumulated, result.usage)
            self.last_usage = combined
            return result.model_copy(update={"usage": combined})
        raise ContextResearchError("OpenRouter context research failed after retry")

    def _research_once(self, inputs: ResearchInputs) -> ContextResearchResult:
        self.last_usage = ResearchUsage()
        queries = build_search_queries(inputs, limit=self._max_search_queries)
        parameters: dict[str, Any] = {
            "engine": self._engine,
            "max_results": self._max_results_per_query,
            "max_total_results": self._max_search_results,
            "search_context_size": "low",
        }
        if inputs.allowed_domains:
            parameters["allowed_domains"] = inputs.allowed_domains

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(inputs, queries)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "timeout": 45,
            "extra_body": {
                "tools": [
                    {"type": "openrouter:web_search", "parameters": parameters}
                ]
            },
        }
        if self._extra_headers:
            kwargs["extra_headers"] = self._extra_headers

        try:
            response = self._client.chat.completions.create(**kwargs)
        except (OpenAIError, TimeoutError) as exc:
            raise ContextResearchError(
                f"OpenRouter context research failed: {type(exc).__name__}"
            ) from exc

        usage = _parse_usage(getattr(response, "usage", None))
        self.last_usage = usage

        if not response.choices:
            raise ContextResearchError("OpenRouter context research returned no choice")
        message = response.choices[0].message
        content = message.content
        if not content:
            raise ContextResearchError("OpenRouter context research returned empty content")

        try:
            raw_output = _ProviderResearchOutput.model_validate_json(content)
        except ValidationError as exc:
            raise ContextResearchError("OpenRouter context research returned invalid JSON") from exc
        if not set(raw_output.queries).issubset(queries):
            raise ContextResearchError("OpenRouter reported a query outside the allowlist")

        if usage.web_search_requests > self._max_search_queries:
            raise ContextResearchError("OpenRouter exceeded the search-query limit")

        annotations = list(getattr(message, "annotations", None) or [])
        citations = _normalize_citations(annotations, retrieved_at=self._clock())
        if len(citations) > self._max_search_results:
            raise ContextResearchError("OpenRouter exceeded the citation-result limit")
        if not citations and usage.web_search_requests == 0:
            raise ContextResearchError("Response did not use the web-search server tool")

        citation_ids_by_url = {citation.url: citation.citation_id for citation in citations}
        candidates: list[ResearchCandidateDraft] = []
        for candidate in raw_output.candidates:
            citation_ids = [
                citation_ids_by_url[url]
                for url in dict.fromkeys(candidate.citation_urls)
                if url in citation_ids_by_url
            ]
            if not citation_ids:
                continue
            candidates.append(
                ResearchCandidateDraft(
                    candidate_key=candidate.candidate_key,
                    title=candidate.title,
                    event_at=candidate.event_at,
                    citation_ids=citation_ids,
                    matched_entities=candidate.matched_entities,
                    matched_condition=candidate.matched_condition,
                    temporal_relation=candidate.temporal_relation,
                )
            )

        return ContextResearchResult(
            model=self._model,
            queries=raw_output.queries,
            citations=citations,
            candidates=candidates,
            usage=usage,
        )


def build_context_research_client(
    api_key: str,
    model: str,
    *,
    engine: str = "auto",
    max_search_queries: int = CONTEXT_MAX_SEARCH_QUERIES,
    max_search_results: int = CONTEXT_MAX_SEARCH_RESULTS,
    max_results_per_query: int = CONTEXT_MAX_RESULTS_PER_QUERY,
    extra_headers: dict[str, str] | None = None,
) -> OpenRouterContextResearchClient:
    """Explicitly construct the paid-capable OpenRouter research client."""
    return OpenRouterContextResearchClient(
        OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL),
        model,
        engine=engine,
        max_search_queries=max_search_queries,
        max_search_results=max_search_results,
        max_results_per_query=max_results_per_query,
        extra_headers=extra_headers,
    )


def build_context_research_client_from_settings(
    app_settings: Settings,
) -> OpenRouterContextResearchClient:
    """Build from settings without logging or exposing the selected key."""
    key = app_settings.openrouter_api_key
    if not key and app_settings.openai_api_key and app_settings.openai_api_key.startswith("sk-or-"):
        key = app_settings.openai_api_key
    if not key:
        raise ContextResearchError("OpenRouter API key is not configured")

    headers: dict[str, str] = {}
    if app_settings.openrouter_http_referer:
        headers["HTTP-Referer"] = app_settings.openrouter_http_referer
    if app_settings.openrouter_app_title:
        headers["X-OpenRouter-Title"] = app_settings.openrouter_app_title
    return build_context_research_client(
        key,
        app_settings.context_research_model,
        engine=app_settings.context_search_engine,
        max_search_queries=app_settings.context_max_search_queries,
        max_search_results=app_settings.context_max_search_results,
        max_results_per_query=app_settings.context_max_results_per_query,
        extra_headers=headers,
    )
