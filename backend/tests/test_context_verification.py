"""TASK-059 deterministic and independent-verifier tests with fixed fixtures."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchInputs,
    ResearchUsage,
)
from app.core.context_verification import (
    ContextVerificationError,
    IndependentVerifierClient,
    canonicalize_url,
    deterministic_gate,
    verify_research_result,
)

NOW = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
EVENT_AT = datetime(2026, 7, 11, 8, 0, tzinfo=UTC)
CONDITION = "Published condition is confirmed"
ENTITY = "Published condition"


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
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
        "title": "Will the published condition be confirmed?",
        "description": "Tracks whether the Published condition is confirmed.",
        "category": "technology",
        "tracked_condition": CONDITION,
        "end_date": NOW + timedelta(days=30),
        "resolution_source": "https://example.gov/policy",
        "current_value": 0.63,
        "change_24h": 0.08,
        "change_7d": 0.11,
        "inflection_at": EVENT_AT,
        "search_window_start": NOW - timedelta(hours=12),
        "search_window_end": NOW + timedelta(hours=12),
        "allowed_domains": ["example.gov"],
    }
    values.update(overrides)
    return ResearchInputs(**values)


def _citation(
    citation_id: str = "citation:official",
    *,
    url: str = "https://example.gov/update?utm_source=test",
    title: str = "Published condition update July 11, 2026",
    content: str = "Published condition is confirmed in the record dated July 11, 2026.",
    content_hash: str | None = None,
) -> NormalizedCitation:
    return NormalizedCitation(
        citation_id=citation_id,
        url=url,
        canonical_url=url,
        title=title,
        domain=url.split("/")[2],
        content_excerpt=content,
        content_hash=content_hash or hashlib.sha256(content.encode()).hexdigest(),
        retrieved_at=NOW,
    )


def _candidate(key: str = "candidate:1", **overrides) -> ResearchCandidateDraft:
    values = {
        "candidate_key": key,
        "title": "Official update recorded",
        "event_at": EVENT_AT,
        "citation_ids": ["citation:official"],
        "matched_entities": [ENTITY],
        "matched_condition": CONDITION,
        "temporal_relation": "same_window",
    }
    values.update(overrides)
    return ResearchCandidateDraft(**values)


def _research(candidates=None, citations=None, model="openai/gpt-4o-mini"):
    return ContextResearchResult(
        model=model,
        queries=["bounded query"],
        citations=citations if citations is not None else [_citation()],
        candidates=candidates if candidates is not None else [_candidate()],
        usage=ResearchUsage(web_search_requests=1),
    )


def _output(
    key="candidate:1",
    *,
    accepted=True,
    condition_match=True,
    date_match=True,
    source_supported=True,
    unsupported_claims=None,
    conflicting_citation_ids=None,
    summary="공식 출처는 2026-07-11에 추적 조건 관련 공개 정보를 기록했습니다.",
    reason_code="primary_source_direct_match",
):
    return {
        "candidate_key": key,
        "accepted": accepted,
        "condition_match": condition_match,
        "date_match": date_match,
        "source_supported": source_supported,
        "unsupported_claims": unsupported_claims or [],
        "conflicting_citation_ids": conflicting_citation_ids or [],
        "neutral_summary_ko": summary,
        "reason_code": reason_code,
    }


def _response(outputs=None, *, extra=None):
    payload = {"verifications": outputs if outputs is not None else [_output()]}
    if extra:
        payload.update(extra)
    message = SimpleNamespace(content=json.dumps(payload, ensure_ascii=False))
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _verifier(response=None, *, error=None, research_model="openai/gpt-4o-mini"):
    fake = FakeClient(response=response or _response(), error=error)
    verifier = IndependentVerifierClient(
        fake,
        "anthropic/claude-verifier",
        research_model=research_model,
    )
    return verifier, fake


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "HTTPS://WWW.Example.GOV:443/a//b/?utm_source=x&b=2&a=1#fragment",
            "https://www.example.gov/a/b?a=1&b=2",
        ),
        ("http://example.com:80/", "http://example.com/"),
        ("file:///tmp/source", None),
        ("https://user:secret@example.com/path", None),
    ],
)
def test_canonicalize_url_is_deterministic_and_rejects_unsafe_inputs(raw, expected):
    assert canonicalize_url(raw) == expected


def test_official_single_source_passes_hard_gate_and_independent_verification():
    verifier, fake = _verifier()

    result = verify_research_result(_inputs(), _research(), verifier)

    assert len(result.verified) == 1
    decision = result.verified[0]
    assert decision.reason_code == "primary_source_direct_match"
    assert decision.sources[0].source_type == "official"
    assert decision.evidence_hash
    request = fake.completions.calls[0]
    assert "tools" not in request
    assert "extra_body" not in request
    assert "content_excerpt" in request["messages"][1]["content"]


def test_two_independent_sources_pass_when_domains_and_content_are_distinct():
    citations = [
        _citation(
            "citation:a",
            url="https://news-a.example/story",
            content="Published condition is confirmed in the July 11, 2026 public record A.",
        ),
        _citation(
            "citation:b",
            url="https://news-b.example/report",
            content="On July 11, 2026 the Published condition is confirmed in public record B.",
        ),
    ]
    candidate = _candidate(citation_ids=["citation:a", "citation:b"])
    verifier, _ = _verifier()

    result = verify_research_result(
        _inputs(allowed_domains=[], resolution_source=None),
        _research(candidates=[candidate], citations=citations),
        verifier,
    )

    assert result.verified[0].sources[0].source_type == "independent_secondary"
    assert {source.domain for source in result.verified[0].sources} == {
        "news-a.example",
        "news-b.example",
    }


def test_republished_same_content_does_not_count_as_independent_sources():
    content = "Published condition is confirmed in the record dated July 11, 2026."
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    citations = [
        _citation(
            "citation:a",
            url="https://news-a.example/story",
            content=content,
            content_hash=content_hash,
        ),
        _citation(
            "citation:b",
            url="https://news-b.example/reprint",
            content=content,
            content_hash=content_hash,
        ),
    ]
    gate = deterministic_gate(
        _inputs(allowed_domains=[], resolution_source=None),
        _candidate(citation_ids=["citation:a", "citation:b"]),
        citations,
    )

    assert gate.passed is False
    assert gate.reason_code == "insufficient_independent_sources"


def test_republished_content_with_only_spacing_changes_is_not_independent():
    citations = [
        _citation(
            "citation:a",
            url="https://news-a.example/story",
            content="Published condition is confirmed on July 11, 2026.",
        ),
        _citation(
            "citation:b",
            url="https://news-b.example/reprint",
            content="Published   condition is confirmed on July 11, 2026.",
        ),
    ]

    gate = deterministic_gate(
        _inputs(allowed_domains=[], resolution_source=None),
        _candidate(citation_ids=["citation:a", "citation:b"]),
        citations,
    )

    assert gate.reason_code == "insufficient_independent_sources"


def test_market_and_forecast_pages_never_count_as_public_evidence():
    citation = _citation(url="https://polymarket.com/event/example-market")

    gate = deterministic_gate(
        _inputs(allowed_domains=[], resolution_source=None),
        _candidate(),
        [citation],
    )

    assert gate.passed is False
    assert gate.reason_code == "market_or_forecast_page"


@pytest.mark.parametrize(
    ("candidate", "reason"),
    [
        (_candidate(event_at=NOW + timedelta(days=2)), "event_date_outside_window"),
        (_candidate(event_at=None), "missing_event_date"),
        (_candidate(matched_entities=["Invented Agency"]), "entity_mismatch"),
        (_candidate(matched_condition="Unrelated condition"), "condition_mismatch"),
        (_candidate(title="Invented Agency Announces Update"), "unsupported_proper_noun"),
        (_candidate(title="Update caused by the movement"), "unsafe_relationship_language"),
        (_candidate(citation_ids=["citation:invented"]), "missing_annotation_evidence"),
    ],
)
def test_hard_gate_rejects_model_inventions_and_unsafe_relationships(candidate, reason):
    gate = deterministic_gate(_inputs(), candidate, [_citation()])

    assert gate.passed is False
    assert gate.reason_code == reason


def test_source_date_conflict_rejects_candidate():
    citation = _citation(
        title="Published condition update",
        content="Published condition is confirmed in the record dated July 10, 2026.",
    )
    gate = deterministic_gate(_inputs(), _candidate(), [citation])

    assert gate.passed is False
    assert gate.reason_code == "conflicting_source_date"


def test_model_cannot_promote_a_hard_gate_failure():
    verifier, fake = _verifier()

    result = verify_research_result(
        _inputs(),
        _research(candidates=[_candidate(matched_entities=["Invented Agency"])]),
        verifier,
    )

    assert result.decisions[0].verification_state == "rejected"
    assert result.decisions[0].evidence_hash
    assert fake.completions.calls == []


@pytest.mark.parametrize(
    "output",
    [
        _output(accepted=False),
        _output(condition_match=False),
        _output(unsupported_claims=["unsupported detail"]),
        _output(conflicting_citation_ids=["citation:official"]),
        _output(summary="이 공개 정보 때문에 관찰값이 변했습니다."),
        _output(summary="현실의 결과가 확정되었다고 기록했습니다."),
        _output(summary="공식 출처는 2026-07-12에 공개 정보를 기록했습니다."),
        _output(summary="Invented Agency는 2026-07-11에 공개 정보를 기록했습니다."),
    ],
)
def test_verifier_disagreement_or_new_claims_are_withheld(output):
    verifier, _ = _verifier(_response([output]))

    result = verify_research_result(_inputs(), _research(), verifier)

    assert result.decisions[0].verification_state == "withheld"
    assert result.decisions[0].neutral_summary_ko is None


def test_verifier_model_must_use_a_different_provider_family():
    with pytest.raises(ContextVerificationError, match="different provider family"):
        IndependentVerifierClient(
            FakeClient(),
            "openai/gpt-verifier",
            research_model="openai/gpt-research",
        )


def test_verifier_malformed_output_and_timeout_fail_closed_without_secrets():
    malformed, _ = _verifier(
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"wrong": []}'))])
    )
    with pytest.raises(ContextVerificationError, match="invalid JSON"):
        verify_research_result(_inputs(), _research(), malformed)

    timed_out, _ = _verifier(error=TimeoutError("secret prompt"))
    with pytest.raises(ContextVerificationError) as raised:
        verify_research_result(_inputs(), _research(), timed_out)
    assert "secret" not in str(raised.value)


def test_verifier_candidate_set_must_match_exactly():
    verifier, _ = _verifier(_response([_output(key="candidate:other")]))

    with pytest.raises(ContextVerificationError, match="mismatched candidate set"):
        verify_research_result(_inputs(), _research(), verifier)


def test_rule_and_verifier_limits_are_deterministic():
    candidates = [_candidate(f"candidate:{index}") for index in range(9)]
    outputs = [_output(key=f"candidate:{index}") for index in range(5)]
    verifier, fake = _verifier(_response(outputs))

    result = verify_research_result(
        _inputs(),
        _research(candidates=candidates),
        verifier,
    )

    assert len(result.verified) == 5
    assert [item.reason_code for item in result.decisions[5:8]] == ["verifier_candidate_limit"] * 3
    assert result.decisions[8].reason_code == "rule_passing_candidate_limit"
    sent = json.loads(fake.completions.calls[0]["messages"][1]["content"].split("\n", 1)[1])
    assert len(sent) == 5


def test_duplicate_research_candidate_keys_fail_closed():
    verifier, _ = _verifier()
    research = _research(candidates=[_candidate(), _candidate()])

    with pytest.raises(ContextVerificationError, match="duplicate candidate keys"):
        verify_research_result(_inputs(), research, verifier)
