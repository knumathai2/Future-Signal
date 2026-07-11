"""TASK-058 OpenRouter web-research client tests using fake transports only."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.context_research import (
    ContextResearchError,
    OpenRouterContextResearchClient,
    ResearchInputs,
    build_context_research_client_from_settings,
    build_search_queries,
)

NOW = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
SOURCE_URL = "https://example.gov/releases/update-1"


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.completions = FakeCompletions(response=response, error=error)
        self.chat = SimpleNamespace(completions=self.completions)


def _inputs(**overrides) -> ResearchInputs:
    values = {
        "market_id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        "episode_at": NOW,
        "title": "Will the documented condition be confirmed?",
        "description": "Tracks whether the published condition is confirmed.",
        "category": "technology",
        "tracked_condition": "Published condition is confirmed",
        "end_date": NOW + timedelta(days=30),
        "resolution_source": "https://example.gov/policy",
        "current_value": 0.63,
        "change_24h": 0.08,
        "change_7d": 0.11,
        "inflection_at": NOW - timedelta(hours=1),
        "search_window_start": NOW - timedelta(hours=12),
        "search_window_end": NOW + timedelta(hours=12),
        "allowed_domains": ["example.gov"],
    }
    values.update(overrides)
    return ResearchInputs(**values)


def _provider_content(*, candidates=None, queries=None, extra=None) -> str:
    payload = {
        "queries": queries if queries is not None else build_search_queries(_inputs())[:1],
        "candidates": candidates if candidates is not None else [
            {
                "candidate_key": "candidate:local-1",
                "title": "Official update recorded",
                "event_at": "2026-07-11T08:00:00Z",
                "citation_urls": [SOURCE_URL],
                "matched_entities": ["Published condition"],
                "matched_condition": "Published condition is confirmed",
                "temporal_relation": "same_window",
            }
        ],
    }
    if extra:
        payload.update(extra)
    return json.dumps(payload)


def _annotation(
    url: str = SOURCE_URL,
    *,
    title: str = "Official update",
    content: str = "The source records the published update.",
    flat: bool = False,
):
    citation = {"url": url, "title": title, "content": content}
    if flat:
        return {"type": "url_citation", **citation}
    return {"type": "url_citation", "url_citation": citation}


def _response(
    *,
    content=None,
    annotations=None,
    web_search_requests=1,
    input_tokens=100,
    output_tokens=20,
    cost=0.05,
):
    message = SimpleNamespace(
        content=content if content is not None else _provider_content(),
        annotations=annotations if annotations is not None else [_annotation()],
    )
    usage = {
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "server_tool_use": {"web_search_requests": web_search_requests},
        "cost": cost,
    }
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def _client(response=None, *, error=None, **kwargs):
    fake = FakeClient(response=response, error=error)
    return OpenRouterContextResearchClient(
        fake,
        "openai/gpt-4o-mini",
        clock=lambda: NOW,
        **kwargs,
    ), fake


def test_build_search_queries_is_deterministic_deduplicated_and_bounded():
    queries = build_search_queries(_inputs(), limit=99)

    assert 1 <= len(queries) <= 6
    assert len(queries) == len(set(queries))
    assert any("site:example.gov" in query for query in queries)


@pytest.mark.parametrize("domain", ["https://example.gov", "example.gov/path", ""])
def test_research_inputs_reject_non_domain_filters(domain):
    with pytest.raises(ValidationError):
        _inputs(allowed_domains=[domain])


def test_success_uses_server_tool_and_normalizes_only_annotation_citations():
    client, fake = _client(_response())

    result = client.research(_inputs())

    assert result.model == "openai/gpt-4o-mini"
    assert result.policy_version == "v4"
    assert result.usage.web_search_requests == 1
    assert result.usage.cost_usd == 0.05
    assert len(result.citations) == 1
    citation = result.citations[0]
    assert citation.url == SOURCE_URL
    assert citation.canonical_url == SOURCE_URL
    assert citation.domain == "example.gov"
    assert citation.citation_id == f"citation:{hashlib.sha256(SOURCE_URL.encode()).hexdigest()}"
    assert result.candidates[0].citation_ids == [citation.citation_id]

    request = fake.completions.kwargs
    tool = request["extra_body"]["tools"][0]
    assert tool["type"] == "openrouter:web_search"
    assert tool["parameters"]["max_total_results"] == 30
    assert tool["parameters"]["allowed_domains"] == ["example.gov"]
    assert request["response_format"] == {"type": "json_object"}


def test_flat_annotation_shape_is_supported():
    client, _ = _client(_response(annotations=[_annotation(flat=True)]))

    result = client.research(_inputs())

    assert result.citations[0].title == "Official update"


def test_model_body_url_is_not_evidence_and_candidate_is_filtered():
    body_url = "https://model.invalid/invented"
    content = _provider_content(
        candidates=[
            {
                "candidate_key": "candidate:invented",
                "title": "Invented candidate",
                "event_at": None,
                "citation_urls": [body_url],
                "matched_entities": [],
                "matched_condition": "Invented condition",
                "temporal_relation": "same_window",
            }
        ]
    )
    client, _ = _client(_response(content=content, annotations=[_annotation()]))

    result = client.research(_inputs())

    assert [citation.url for citation in result.citations] == [SOURCE_URL]
    assert result.candidates == []


def test_general_response_without_web_search_fails_closed():
    client, _ = _client(
        _response(content=_provider_content(candidates=[]), annotations=[], web_search_requests=0)
    )

    with pytest.raises(ContextResearchError, match="did not use"):
        client.research(_inputs())


def test_completed_search_with_no_citations_is_normal_empty_result():
    client, _ = _client(
        _response(content=_provider_content(candidates=[]), annotations=[], web_search_requests=1)
    )

    result = client.research(_inputs())

    assert result.citations == []
    assert result.candidates == []


@pytest.mark.parametrize(
    "content",
    [
        "not-json",
        json.dumps({"queries": [], "candidates": [], "extra": True}),
        json.dumps({"queries": ["q"] * 7, "candidates": []}),
    ],
)
def test_malformed_or_out_of_bounds_model_output_fails_closed(content):
    client, _ = _client(_response(content=content))

    with pytest.raises(ContextResearchError, match="invalid JSON"):
        client.research(_inputs())


def test_timeout_is_wrapped_without_prompt_or_key_details():
    client, _ = _client(error=TimeoutError("secret prompt and key"))

    with pytest.raises(ContextResearchError) as raised:
        client.research(_inputs())

    assert "secret" not in str(raised.value)
    assert "TimeoutError" in str(raised.value)


def test_search_request_count_above_six_fails_closed():
    client, _ = _client(_response(web_search_requests=7))

    with pytest.raises(ContextResearchError, match="search-query limit"):
        client.research(_inputs())


def test_reported_query_outside_metadata_allowlist_fails_closed():
    client, _ = _client(_response(content=_provider_content(queries=["unbounded query"])))

    with pytest.raises(ContextResearchError, match="outside the allowlist"):
        client.research(_inputs())


def test_more_than_thirty_unique_citations_fails_closed():
    annotations = [
        _annotation(url=f"https://example.gov/source-{index}") for index in range(31)
    ]
    client, _ = _client(_response(annotations=annotations))

    with pytest.raises(ContextResearchError, match="citation-result limit"):
        client.research(_inputs())


def test_duplicate_annotations_keep_one_citation_with_longest_excerpt():
    annotations = [
        _annotation(content="short"),
        _annotation(content="a longer extractive excerpt"),
    ]
    client, _ = _client(_response(annotations=annotations))

    result = client.research(_inputs())

    assert len(result.citations) == 1
    assert result.citations[0].content_excerpt == "a longer extractive excerpt"


def test_invalid_or_titleless_annotations_are_ignored():
    annotations = [
        _annotation(url="file:///tmp/source"),
        _annotation(title=""),
    ]
    client, _ = _client(
        _response(content=_provider_content(candidates=[]), annotations=annotations)
    )

    result = client.research(_inputs())

    assert result.citations == []


def test_constructor_clamps_request_limits_to_approved_maxima():
    client, fake = _client(
        _response(),
        max_search_queries=99,
        max_search_results=99,
        max_results_per_query=99,
    )

    client.research(_inputs())
    parameters = fake.completions.kwargs["extra_body"]["tools"][0]["parameters"]

    assert parameters["max_total_results"] == 30
    assert parameters["max_results"] == 25


def test_settings_clamp_environment_limits_and_invalid_engine(monkeypatch):
    monkeypatch.setenv("CONTEXT_MAX_SEARCH_QUERIES", "100")
    monkeypatch.setenv("CONTEXT_MAX_SEARCH_RESULTS", "100")
    monkeypatch.setenv("CONTEXT_MAX_RESULTS_PER_QUERY", "100")
    monkeypatch.setenv("CONTEXT_SEARCH_ENGINE", "unknown")

    settings = Settings()

    assert settings.context_max_search_queries == 6
    assert settings.context_max_search_results == 30
    assert settings.context_max_results_per_query == 25
    assert settings.context_search_engine == "auto"


def test_settings_builder_requires_openrouter_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ContextResearchError, match="not configured"):
        build_context_research_client_from_settings(Settings())
