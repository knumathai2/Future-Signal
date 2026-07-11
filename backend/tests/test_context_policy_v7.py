"""TASK-103 A-D source classification and conditional verifier routing."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.context_policy_v7 import (
    V7ContextPolicyError,
    V7VerifierDecision,
    apply_v7_conditional_verifier,
    classify_v7_candidate,
    collect_v7_context,
)
from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchInputs,
    ResearchUsage,
)

NOW = datetime(2026, 7, 11, 11, 0, tzinfo=UTC)


def _inputs(**overrides) -> ResearchInputs:
    values = {
        "market_id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        "episode_at": NOW,
        "title": "Will the agency publish the documented decision?",
        "description": "Tracks whether the agency publishes the documented decision.",
        "category": "policy",
        "tracked_condition": "Agency publishes the documented decision",
        "end_date": NOW + timedelta(days=30),
        "resolution_source": "https://agency.gov/rules",
        "current_value": 0.55,
        "change_24h": 0.02,
        "change_7d": 0.03,
        "inflection_at": None,
        "search_window_start": NOW - timedelta(days=1),
        "search_window_end": NOW,
        "allowed_domains": ["agency.gov"],
    }
    values.update(overrides)
    return ResearchInputs(**values)


def _citation(
    citation_id: str,
    domain: str,
    *,
    excerpt: str = "The agency publishes the documented decision and schedule.",
) -> NormalizedCitation:
    url = f"https://{domain}/document"
    return NormalizedCitation(
        citation_id=citation_id,
        url=url,
        canonical_url=url,
        title="Agency documented decision",
        domain=domain,
        content_excerpt=excerpt,
        content_hash=hashlib.sha256(excerpt.encode()).hexdigest(),
        retrieved_at=NOW,
    )


def _candidate(*citation_ids: str, condition: str | None = None) -> ResearchCandidateDraft:
    return ResearchCandidateDraft(
        candidate_key="candidate:1",
        title="Agency decision update",
        event_at=NOW - timedelta(hours=1),
        citation_ids=list(citation_ids),
        matched_entities=["agency"],
        matched_condition=condition or "Agency publishes the documented decision",
        temporal_relation="same_window",
    )


class FakeVerifier:
    model = "anthropic/claude-test"

    def __init__(self, accepted=True):
        self.accepted = accepted
        self.calls = 0

    def verify(self, candidate):
        self.calls += 1
        refs = [
            claim.ref for source in candidate.public_sources for claim in source.supported_claims
        ]
        return V7VerifierDecision(
            candidate_key=candidate.candidate_key,
            accepted=self.accepted,
            supported_claim_refs=refs,
            reason_code="supported" if self.accepted else "ambiguous",
        )


class FakeResearchClient:
    model = "openai/research-test"

    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.inputs = None

    def research(self, inputs):
        self.calls += 1
        self.inputs = inputs
        return self.result


def test_official_source_is_level_a_and_needs_no_verifier():
    citation = _citation("citation:a", "agency.gov")
    result = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(),
    )
    assert result.state == "accepted"
    assert result.public_sources[0].level == "A"
    assert result.verifier_triggers == []


def test_established_source_is_level_b_and_supports_exact_claim():
    citation = _citation("citation:b", "reliable.example")
    result = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
        established_domains={"reliable.example"},
    )
    assert result.state == "accepted"
    assert result.public_sources[0].level == "B"
    assert result.public_sources[0].supported_claims[0].citation_id == "citation:b"


def test_level_c_is_accepted_for_supporting_context_but_material_use_routes_verifier():
    citation = _citation("citation:c", "specialist.example")
    supporting = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
    )
    material = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
        material_to_summary=True,
    )
    assert supporting.state == "accepted"
    assert supporting.public_sources[0].level == "C"
    assert material.state == "withheld"
    assert "material_level_c_claim" in material.verifier_triggers


@pytest.mark.parametrize(
    ("domain", "excerpt"),
    [
        ("polymarket.com", "Agency publishes the documented decision."),
        ("unknown.example", ""),
        ("unknown.example", "A completely unrelated sports result."),
    ],
)
def test_level_d_sources_never_become_public(domain, excerpt):
    citation = _citation("citation:d", domain, excerpt=excerpt)
    result = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
    )
    assert result.state == "rejected"
    assert result.public_sources == []
    assert result.sources[0].level == "D"


def test_conflict_and_high_impact_secondary_claims_route_conditionally():
    citation = _citation(
        "citation:conflict",
        "reliable.example",
        excerpt="The agency approved and publishes the documented decision.",
    )
    result = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
        established_domains={"reliable.example"},
        conflicting_citation_ids={citation.citation_id},
    )
    assert result.state == "withheld"
    assert result.verifier_triggers == ["high_impact_claim", "source_conflict"]


def test_triggered_candidate_fails_closed_without_verifier_and_accepts_independent_pass():
    citation = _citation("citation:c", "specialist.example")
    candidate = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
        material_to_summary=True,
    )
    assert apply_v7_conditional_verifier(
        candidate, None, research_model="openai/research"
    ).reason_code == "verifier_unavailable"

    verifier = FakeVerifier()
    accepted = apply_v7_conditional_verifier(
        candidate, verifier, research_model="openai/research"
    )
    assert accepted.state == "accepted"
    assert verifier.calls == 1


def test_same_provider_family_is_rejected_for_conditional_verification():
    citation = _citation("citation:c", "specialist.example")
    candidate = classify_v7_candidate(
        _candidate(citation.citation_id),
        {citation.citation_id: citation},
        _inputs(allowed_domains=[]),
        material_to_summary=True,
    )
    verifier = FakeVerifier()
    verifier.model = "openai/verifier"
    with pytest.raises(V7ContextPolicyError):
        apply_v7_conditional_verifier(
            candidate,
            verifier,
            research_model="openai/research",
        )


def test_collection_calls_research_once_and_routes_only_triggered_candidate():
    citation = _citation("citation:c", "specialist.example")
    research = ContextResearchResult(
        model="openai/research-test",
        queries=["agency documented decision"],
        citations=[citation],
        candidates=[_candidate(citation.citation_id)],
        usage=ResearchUsage(input_tokens=10, output_tokens=5, web_search_requests=1),
    )
    client = FakeResearchClient(research)
    verifier = FakeVerifier()
    result = collect_v7_context(
        _inputs(allowed_domains=[]),
        client,
        verifier=verifier,
        material_candidate_keys={"candidate:1"},
    )
    assert client.calls == 1
    assert client.inputs.search_window_start == NOW - timedelta(days=30)
    assert client.inputs.inflection_at is None
    assert verifier.calls == 1
    assert len(result.accepted) == 1
    assert result.policy_version == "v7-source-level-1"
