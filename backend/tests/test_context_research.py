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
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
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
        "candidates": candidates
        if candidates is not None
        else [
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


def test_search_queries_prioritize_entity_condition_window_and_official_domain():
    queries = build_search_queries(
        _inputs(
            title="Will JD Vance win the US Presidential Election?",
            description="Tracks JD Vance and the documented presidential election result.",
            tracked_condition="JD Vance wins the US Presidential Election",
            allowed_domains=["fec.gov", "archives.gov"],
        )
    )

    joined = "\n".join(queries)
    assert '"JD Vance"' in joined
    assert "2026-07-10" in joined and "2026-07-11" in joined
    assert "site:fec.gov" in joined or "site:archives.gov" in joined
    assert any("official announcement document" in query for query in queries)


def test_search_queries_add_cross_wording_alias_for_diplomatic_issue():
    queries = build_search_queries(
        _inputs(
            title="미·러 핵 합의가 연말까지 이뤄질까?",
            description="미국과 러시아의 핵 합의 여부를 다루는 이슈입니다.",
            category="외교",
            tracked_condition="미국과 러시아가 핵 합의를 공식 발표함",
            allowed_domains=[],
            resolution_source=None,
        )
    )

    assert any(
        '"United States Russia nuclear agreement"' in query for query in queries
    )


def test_generic_stored_condition_does_not_become_search_entity_or_anchor():
    queries = build_search_queries(
        _inputs(
            title="Will Hamas agree to disarm by December 31?",
            description="Tracks reflected expectation in public data.",
            tracked_condition=(
                "Tracks reflected expectation in public prediction-market data. "
                "Interpret changes with caution. Tracked outcome: Yes."
            ),
            allowed_domains=[],
            resolution_source=None,
        )
    )

    joined = "\n".join(queries)
    assert '"Hamas"' in joined
    assert '"Interpret"' not in joined
    assert "reflected expectation interpret caution" not in joined


@pytest.mark.parametrize("domain", ["https://example.gov", "example.gov/path", ""])
def test_research_inputs_reject_non_domain_filters(domain):
    with pytest.raises(ValidationError):
        _inputs(allowed_domains=[domain])


def test_research_inputs_and_candidates_require_timezone_aware_dates():
    with pytest.raises(ValidationError, match="timezone"):
        _inputs(episode_at=datetime(2026, 7, 11, 9, 0, 0))

    content = _provider_content()
    content = content.replace("2026-07-11T08:00:00Z", "2026-07-11T08:00:00")
    client, _ = _client(_response(content=content))
    result = client.research(_inputs())
    assert result.candidates[0].event_at is None


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
    assert "response_format" not in request
    assert request["tool_choice"] == "required"
    assert "Market listing, price, forecast, and mirror pages" in request["messages"][0]["content"]


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


def test_natural_language_search_response_uses_exact_annotation_fallback():
    client, _ = _client(
        _response(
            content="The agency published an update with a source citation.",
            annotations=[
                _annotation(content="The agency published the documented update.")
            ],
        )
    )

    result = client.research(_inputs())

    assert result.queries == build_search_queries(_inputs())
    assert len(result.candidates) == 1
    assert result.candidates[0].citation_ids == [result.citations[0].citation_id]
    assert result.candidates[0].matched_condition == result.citations[0].content_excerpt


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
    client, _ = _client(_response(content=content, annotations=[]))

    with pytest.raises(ContextResearchError, match="invalid JSON"):
        client.research(_inputs())


def test_invalid_json_retries_once_and_retains_billed_usage():
    client, fake = _client(
        _response(content="not-json", annotations=[], cost=0.05)
    )

    with pytest.raises(ContextResearchError, match="invalid JSON"):
        client.research(_inputs())

    assert fake.completions.calls == 2
    assert client.last_usage.input_tokens == 200
    assert client.last_usage.output_tokens == 40
    assert client.last_usage.web_search_requests == 2
    assert client.last_usage.cost_usd == 0.1
    assert fake.completions.kwargs["extra_body"]["plugins"][0]["id"] == "web"
    assert "engine" not in fake.completions.kwargs["extra_body"]["plugins"][0]
    assert "tool_choice" not in fake.completions.kwargs


def test_current_server_tool_usage_detail_shape_is_counted():
    response = _response()
    response.usage.pop("server_tool_use")
    response.usage["server_tool_use_details"] = {"web_search_requests": 2}
    client, _ = _client(response)

    result = client.research(_inputs())

    assert result.usage.web_search_requests == 2


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


def test_reported_query_count_respects_configured_runtime_limit():
    queries = [
        "Technology authority release",
        "Technology confirmation record",
    ]
    client, _ = _client(
        _response(content=_provider_content(queries=queries), annotations=[]),
        max_search_queries=1,
    )

    with pytest.raises(ContextResearchError, match="query audit data"):
        client.research(_inputs())


def test_reformulated_query_with_normalized_metadata_overlap_is_accepted():
    query = "Technology authority confirmation release"
    client, _ = _client(_response(content=_provider_content(queries=[query])))

    result = client.research(_inputs())

    assert result.queries == [query]
    assert client.last_queries == [query]


@pytest.mark.parametrize(
    "queries",
    [
        ["celebrity sports score"],
        ["official latest update"],
        ["   "],
        ["technology authority", "technology authority"],
    ],
)
def test_reported_query_without_distinct_market_metadata_overlap_fails_closed(queries):
    client, _ = _client(
        _response(content=_provider_content(queries=queries), annotations=[])
    )

    with pytest.raises(ContextResearchError, match="query audit data|metadata scope"):
        client.research(_inputs())

    assert client.last_queries == queries


def test_invalid_body_query_audit_with_annotations_uses_bounded_scope_queries():
    client, _ = _client(
        _response(content=_provider_content(queries=["celebrity sports score"]))
    )

    result = client.research(_inputs())

    assert result.queries == build_search_queries(_inputs())
    assert len(result.candidates) == 1


def test_more_than_thirty_unique_citations_fails_closed():
    annotations = [_annotation(url=f"https://example.gov/source-{index}") for index in range(31)]
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
    monkeypatch.setenv("CONTEXT_BUDGET_USD", "1000")
    monkeypatch.setenv("CONTEXT_COST_RESERVATION_USD", "1000")

    settings = Settings()

    assert settings.context_max_search_queries == 6
    assert settings.context_max_search_results == 30
    assert settings.context_max_results_per_query == 25
    assert settings.context_search_engine == "auto"
    assert settings.context_budget_usd == 100
    assert settings.context_cost_reservation_usd == 100


def test_settings_builder_requires_openrouter_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ContextResearchError, match="not configured"):
        build_context_research_client_from_settings(Settings())
